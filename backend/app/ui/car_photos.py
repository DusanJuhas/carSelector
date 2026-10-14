"""Car photos shown on result cards, served as static files from
`storage/car_photos/` (see storage/README.md). A hand-picked set of freely licensed images
from Wikimedia Commons - the catalog itself has no image source (see
doc/api-contract.md's `thumbnail_url` note), so a model without an entry
here keeps the card's striped placeholder.

Every entry carries its attribution: Creative Commons licences (CC BY,
CC BY-SA) require showing the author, licence and source next to the
image, which `results_grid.car_card` does. Files are Commons' small
(~320px) thumbnails - enough for a 230px-wide card.
"""

from dataclasses import dataclass

from nicegui import app

from app.core.config import CAR_PHOTOS_DIR as PHOTOS_DIR

PHOTOS_URL = "/car-photos"


@dataclass(frozen=True)
class CarPhoto:
    """One photo and its attribution.

    Attributes:
        file: File name inside `PHOTOS_DIR`.
        author: Author as named on the Commons file page.
        license: Short licence name, e.g. "CC0" or "CC BY-SA 4.0".
        source_url: The Commons file page (author, licence, original).
    """

    file: str
    author: str
    license: str
    source_url: str

    @property
    def url(self) -> str:
        """The URL the browser loads the image from."""
        return f"{PHOTOS_URL}/{self.file}"


# Keyed by the catalog's exact (brand, model) names.
CAR_PHOTOS: dict[tuple[str, str], CarPhoto] = {
    ("Toyota", "RAV4"): CarPhoto(
        file="toyota-rav4.jpg",
        author="TTTNIS",
        license="CC0",
        source_url="https://commons.wikimedia.org/wiki/File:2021_Toyota_RAV4_PHV.jpg",
    ),
}


def photo_for(brand: str, model: str) -> CarPhoto | None:
    """Looks up a model's photo.

    Args:
        brand: Catalog brand name, e.g. "Toyota".
        model: Catalog model name, e.g. "RAV4".

    Returns:
        The photo, or `None` if the model has none (the card shows a
        placeholder).
    """
    return CAR_PHOTOS.get((brand, model))


def register_car_photos() -> None:
    """Serves `PHOTOS_DIR` at `PHOTOS_URL`. Called once at startup (see
    `app/main.py`)."""
    app.add_static_files(PHOTOS_URL, PHOTOS_DIR)
