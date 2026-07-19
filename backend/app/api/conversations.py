from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import api_error
from app.schemas.conversation import ConversationStartResponse, MessageRequest, MessageResponse
from app.services import conversation

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationStartResponse, status_code=201)
def start_conversation() -> ConversationStartResponse:
    conversation_id, intro_message = conversation.start_conversation()
    return ConversationStartResponse(conversation_id=conversation_id, intro_message=intro_message)


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
    conversation_id: str, body: MessageRequest, db: Session = Depends(get_db)
) -> MessageResponse:
    try:
        return conversation.handle_message(db, conversation_id, body.text)
    except conversation.UnknownConversationError:
        api_error(404, "conversation_not_found", f"No conversation with id {conversation_id}")
    except RuntimeError as exc:
        # AI layer not configured (missing ANTHROPIC_API_KEY) - see
        # app/ai/client.py.
        api_error(503, "ai_not_configured", str(exc))
