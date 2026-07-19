"""Generates a short, honest per-vehicle explanation once the
recommendation engine has already ranked results - see the
drivewise-ai-recommendations skill. Grounded only in the vehicle's actual
matched attributes; never invents specs.

NOTE: untested against a live API - see requirement_interpreter.py.
"""

from app.ai.client import get_client
from app.core.config import CLAUDE_MODEL
from app.schemas.requirement import StructuredRequirements
from app.schemas.vehicle import VehicleSummary

SYSTEM_PROMPT = """You explain a car recommendation in one short sentence (max ~25 words).
Ground the explanation only in the vehicle facts given to you - never invent a feature, spec, or
price the vehicle doesn't have. Plain, factual tone, no marketing language.
"""


def explain(vehicle: VehicleSummary, requirements: StructuredRequirements) -> str:
    client = get_client()
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
