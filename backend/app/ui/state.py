"""Per-connection UI state, replacing the former frontend's two Zustand
stores (`conversationStore`, `catalogStore`) plus the side-effect logic
that lived in `hooks/useConversation.ts` / `hooks/useCatalog.ts` /
`hooks/useVehicleDetail.ts`. A `@ui.page` function's local variables are
already private to one browser connection (NiceGUI's per-client-closure
model - see `app/ui/pages.py`), so these are plain dataclasses instantiated
once per page load, not global state - the direct analogue of a Zustand
store scoped to a single mounted React tree instead of the whole app.

Every service-layer call here goes through `nicegui.run.io_bound` so the
synchronous SQLAlchemy/orchestrator calls never block the event loop other
connections share - see `app/ui/db.py`.
"""

from dataclasses import dataclass, field

from nicegui import run

from app.models.enums import Drivetrain, FuelType
from app.schemas.catalog import BrandRead
from app.schemas.requirement import UserRequirement
from app.schemas.vehicle import VehicleDetail, VehicleSummary
from app.services import catalog
from app.services.conversation import orchestrator
from app.ui import db as ui_db

# Mirrors frontend/src/types/conversation.ts's ChatMessage.
ChatMessage = tuple[str, str]  # (role, text) - role is "user" | "assistant"

PAGE_SIZE = 20


@dataclass
class ConversationState:
    """The chat/narrowing side of the page - AI-driven conversation state.

    Mirrors `conversationStore` + `useConversation`'s combined state and
    behavior. `error` is one of `"ai_not_configured"` | `"unknown_error"`
    | `None` - there's no `"network_error"` case here (unlike the old
    frontend's `ApiError`), since calling the orchestrator in-process has
    no network hop to fail.
    """

    conversation_id: str | None = None
    messages: list[ChatMessage] = field(default_factory=list)
    requirements: list[UserRequirement] = field(default_factory=list)
    cars: list[VehicleSummary] = field(default_factory=list)
    # True once the recommendation engine has actually run at least once
    # (a turn's `searched=True`). Distinguishes "AI hasn't narrowed
    # anything yet" (show the full catalog) from "AI searched and found
    # nothing" (both leave `cars` empty) - only `restart()` clears it.
    has_narrowed: bool = False
    drawer_open: bool = False
    is_loading: bool = False
    is_sending: bool = False
    error: str | None = None

    async def begin(self) -> None:
        """Starts a new conversation and seeds the transcript with its
        opening message. `start_conversation` is pure in-memory
        (uuid + dict), so this calls it directly rather than through
        `run.io_bound`.
        """
        self.is_loading = True
        self.error = None
        try:
            conversation_id, intro_message = orchestrator.start_conversation()
            self.conversation_id = conversation_id
            self.messages = [("assistant", intro_message)]
        except Exception:
            self.error = "unknown_error"
        finally:
            self.is_loading = False

    async def send(self, text: str) -> None:
        """Sends `text` as the user's next message and applies the
        result. No-ops if already sending, the message is blank, or the
        conversation hasn't started yet.

        Args:
            text: The user's message.
        """
        trimmed = text.strip()
        if not trimmed or self.is_sending or self.conversation_id is None:
            return

        self.messages.append(("user", trimmed))
        self.is_sending = True
        self.error = None
        conversation_id = self.conversation_id

        def _send() -> object:
            with ui_db.get_session() as db:
                return orchestrator.handle_message(db, conversation_id, trimmed)

        try:
            result = await run.io_bound(_send)
            self.messages.append(("assistant", result.assistant_text))
            self.requirements = result.requirements
            self.cars = result.vehicles
            self.has_narrowed = self.has_narrowed or result.searched
        except RuntimeError:
            # AI layer not configured (missing ANTHROPIC_API_KEY) - see
            # app/ai/client.py.
            self.error = "ai_not_configured"
        except Exception:
            self.error = "unknown_error"
        finally:
            self.is_sending = False

    async def restart(self) -> None:
        """Abandons the current conversation and starts a fresh one."""
        self.conversation_id = None
        self.messages = []
        self.requirements = []
        self.cars = []
        self.has_narrowed = False
        self.drawer_open = False
        self.error = None
        await self.begin()

    def toggle_drawer(self) -> None:
        """Opens the requirements drawer if closed, closes it if open."""
        self.drawer_open = not self.drawer_open

    def close_drawer(self) -> None:
        """Closes the requirements drawer."""
        self.drawer_open = False


@dataclass
class CatalogState:
    """"Browsing mode" - the paginated full catalog shown before the AI
    has narrowed anything. Mirrors `catalogStore` + `useCatalog`.
    """

    cars: list[VehicleSummary] = field(default_factory=list)
    page: int = 0
    page_size: int = PAGE_SIZE
    total: int = 0
    is_loading: bool = False
    is_loading_more: bool = False
    error: bool = False
    # Catalog-browsing filters (see `app/ui/components/filter_bar.py`) -
    # pushed straight to the backend query rather than applied client-side,
    # the same way `price_asc`/`price_desc`/`alpha` sort does, so `total`
    # and pagination stay correct against the filtered set.
    brand_id: int | None = None
    fuel_type: FuelType | None = None
    drivetrain: Drivetrain | None = None
    brands: list[BrandRead] = field(default_factory=list)

    @property
    def has_more(self) -> bool:
        """True if `load_more` would return anything - `cars` loaded so
        far is fewer than `total` matching rows.
        """
        return len(self.cars) < self.total

    async def load_brands(self) -> None:
        """Loads the brand list once, for the manufacturer filter dropdown.
        Leaves `brands` empty (rather than raising) if the query fails -
        the filter bar just shows no brand options in that case.
        """

        def _load() -> object:
            with ui_db.get_session() as db:
                return catalog.list_brands(db)

        try:
            self.brands = await run.io_bound(_load)
        except Exception:
            self.brands = []

    async def load_first_page(self, sort: str | None) -> None:
        """(Re)loads page 1, replacing whatever's currently loaded -
        called on first mount and whenever `sort` or a filter changes.

        Args:
            sort: Backend sort option (`"price_asc"` | `"price_desc"` |
                `"alpha"`), or `None` for the default order.
        """
        self.is_loading = True
        self.error = False

        def _load() -> object:
            with ui_db.get_session() as db:
                return catalog.list_vehicles(
                    db,
                    brand_id=self.brand_id,
                    fuel_type=self.fuel_type,
                    drivetrain=self.drivetrain,
                    sort=sort,
                    page=1,
                    page_size=self.page_size,
                )

        try:
            result = await run.io_bound(_load)
            self.cars = result.items
            self.page = result.page
            self.total = result.total
        except Exception:
            self.error = True
        finally:
            self.is_loading = False

    async def load_more(self, sort: str | None) -> None:
        """Appends the next page to what's already loaded. No-ops if
        already loading another page or everything is already loaded.

        Args:
            sort: Same backend sort option as the initial load - must
                match, or the appended page could be in a different order.
        """
        if self.is_loading_more or not self.has_more:
            return
        self.is_loading_more = True
        next_page = self.page + 1

        def _load() -> object:
            with ui_db.get_session() as db:
                return catalog.list_vehicles(
                    db,
                    brand_id=self.brand_id,
                    fuel_type=self.fuel_type,
                    drivetrain=self.drivetrain,
                    sort=sort,
                    page=next_page,
                    page_size=self.page_size,
                )

        try:
            result = await run.io_bound(_load)
            self.cars = [*self.cars, *result.items]
            self.page = result.page
            self.total = result.total
        except Exception:
            self.error = True
        finally:
            self.is_loading_more = False


async def fetch_vehicle_detail(configuration_id: int) -> VehicleDetail | None:
    """Loads full detail for one vehicle configuration.

    Args:
        configuration_id: Id of the configuration to load.

    Returns:
        The detail, or `None` if the id doesn't exist or has no current
        price (mirrors `catalog.get_vehicle_detail`'s own `None` case).
    """

    def _load() -> VehicleDetail | None:
        with ui_db.get_session() as db:
            return catalog.get_vehicle_detail(db, configuration_id)

    return await run.io_bound(_load)
