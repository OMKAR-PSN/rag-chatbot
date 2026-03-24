import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.rag.retrieval import query_rag_stream
from app.rag.ingestion import process_and_store_documents
from app.utils.intent_router import get_chitchat_response

router = APIRouter()
logger = logging.getLogger(__name__)


class MessageHistory(BaseModel):
    role: str
    content: str


class UserProfile(BaseModel):
    age: str = ""
    gender: str = ""
    income: str = ""
    caste: str = ""
    location: str = ""


class ChatRequest(BaseModel):
    message: str
    language: str = "English"
    history: list[MessageHistory] = []
    profile: UserProfile | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []


def _sse(data: str) -> str:
    return f"data: {json.dumps({'type': 'chunk', 'data': data})}\n\n"


def _chitchat_stream(text: str):
    """Sync generator — yields an instant SSE response for chitchat."""
    yield _sse(text)


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # ── Fast path: instant reply for greetings / chitchat ────────────────
        instant = get_chitchat_response(request.message)
        if instant:
            logger.debug("Chitchat fast-path for: %s", request.message[:40])
            return StreamingResponse(
                _chitchat_stream(instant),
                media_type="text/event-stream",
            )

        # ── Slow path: full RAG pipeline ─────────────────────────────────────
        history_dicts = [
            {"role": h.role, "content": h.content} for h in request.history
        ]
        profile_dict = request.profile.model_dump() if request.profile else None

        return StreamingResponse(
            query_rag_stream(
                request.message,
                request.language,
                history_dicts,
                profile_dict,
            ),
            media_type="text/event-stream",
        )

    except Exception as e:
        logger.error("Error processing chat request: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/ingest")
async def ingest_documents():
    """Trigger document ingestion manually."""
    success = process_and_store_documents()
    if success:
        return {"status": "success", "message": "Document ingestion completed."}
    return {"status": "warning", "message": "No documents found to ingest."}
