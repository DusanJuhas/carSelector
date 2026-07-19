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
