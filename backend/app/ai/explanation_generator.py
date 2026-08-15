"""Generates a short, honest per-vehicle explanation once the
recommendation engine has already ranked results - see the
drivewise-ai-recommendations skill. Grounded only in the vehicle's actual
matched attributes; never invents specs.

NOTE: untested against a live API - see requirement_interpreter.py.
"""

import anthropic

from app.ai.client import get_client
from app.core.config import CLAUDE_MODEL
from app.schemas.requirement import StructuredRequirements
from app.schemas.vehicle import VehicleSummary

SYSTEM_PROMPT = """You explain a car recommendation in one short sentence (max ~25 words).
Ground the explanation only in the vehicle facts given to you - never invent a feature, spec, or
price the vehicle doesn't have. Plain, factual tone, no marketing language.
"""


class ExplanationGenerator:
    """Wraps one Claude API call that turns a ranked vehicle + the
    requirements it matched into a short, fact-grounded sentence, per
    `drivewise-ai-recommendations`'s Code style section. Stateless beyond
    the injected client - safe to share a single instance across requests
    (see the module-level `generator` singleton at the bottom of this
    file).
    """

    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        """Args:
            client: Anthropic SDK client to use. Defaults to `None`, in
                which case `explain` lazily resolves the shared client
                from `app.ai.client.get_client()` on first use - so
                constructing an `ExplanationGenerator` never fails just
                because `ANTHROPIC_API_KEY` isn't set; only calling
                `explain` does. Pass an explicit client (e.g. a test
                double) to bypass that shared singleton.
        """
        self._client = client

    def _get_client(self) -> anthropic.Anthropic:
        """Returns the injected client, or lazily resolves the shared
        default on first use.

        Returns:
            The Anthropic client this instance uses for API calls.
        """
        if self._client is None:
            self._client = get_client()
        return self._client

    def explain(self, vehicle: VehicleSummary, requirements: StructuredRequirements) -> str:
        """Generates a one-sentence explanation for why `vehicle` was
        recommended, grounded only in its own listed specs and the
        user's stated priorities.

        Args:
            vehicle: The ranked vehicle to explain. Only `brand`, `model`,
                `trim`, `price`, and `specs` are sent to the model -
                nothing is invented beyond what's already on this object.
            requirements: The structured requirements this vehicle was
                matched against; `priorities` is included as context so
                the explanation can reference what the user said mattered.

        Returns:
            A short (~25 words), factual explanation sentence with
            surrounding whitespace stripped.
        """
        client = self._get_client()
        facts = (
            f"Vehicle: {vehicle.brand} {vehicle.model} {vehicle.trim}\n"
            f"Price: {vehicle.price.amount} {vehicle.price.currency}\n"
            f"Specs: {', '.join(vehicle.specs)}\n"
            f"User priorities: {', '.join(requirements.priorities) or 'none stated'}\n"
        )
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=100,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": facts}],
        )
        return "".join(block.text for block in response.content if block.type == "text").strip()


# Shared instance for callers that don't need a custom client (e.g. tests
# injecting a fake) - mirrors get_client()'s cached-singleton shape without
# needing its own cache, since construction here does no I/O.
generator = ExplanationGenerator()
