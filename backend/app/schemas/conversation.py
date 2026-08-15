from typing import Literal

from pydantic import BaseModel

from app.schemas.requirement import StructuredRequirements, UserRequirement
from app.schemas.vehicle import VehicleSummary

ChatRole = Literal["user", "assistant"]


class ChatMessage(BaseModel):
    role: ChatRole
    text: str


class ConversationStartResponse(BaseModel):
    conversation_id: str
    intro_message: str


class MessageRequest(BaseModel):
    text: str


class MessageResponse(BaseModel):
    assistant_text: str
    requirements: list[UserRequirement]
    structured_requirements: StructuredRequirements
    vehicles: list[VehicleSummary]
    # True iff the recommendation engine actually ran this turn (enough was
    # known to search on) - false while the AI is still asking follow-up
    # questions. Distinguishes "haven't searched yet" from "searched and
    # found nothing" for a client showing an unfiltered catalog as a
    # fallback before the first real search (both cases leave `vehicles`
    # empty, but only the second should say "0 matches").
    searched: bool
