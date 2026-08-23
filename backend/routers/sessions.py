"""
Sessions API router — Manage conversations, chat history, and trip plans.
"""
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import database

router = APIRouter()


class CreateSessionRequest(BaseModel):
    title: str | None = None
    destination: str | None = None


class SaveMessageRequest(BaseModel):
    session_id: str
    message_id: str | None = None
    role: str
    content: str
    type: str = "text"
    payload: dict | list | None = None


@router.get("/sessions")
async def get_sessions():
    """List all saved sessions."""
    sessions = await database.list_sessions()
    return {"sessions": sessions}


@router.post("/sessions")
async def create_new_session(req: CreateSessionRequest):
    """Create a new chat/trip session."""
    session_id = str(uuid.uuid4())
    title = req.title or "New Trip Planning"
    await database.save_session(session_id, title, req.destination)
    return {"session_id": session_id, "title": title}


@router.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """Get full message history for a given session."""
    messages = await database.get_session_messages(session_id)
    return {"session_id": session_id, "messages": messages}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    await database.delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}


@router.post("/messages")
async def save_msg(req: SaveMessageRequest):
    """Save an individual message to session history."""
    msg_id = req.message_id or str(uuid.uuid4())
    await database.save_message(
        session_id=req.session_id,
        message_id=msg_id,
        role=req.role,
        content=req.content,
        msg_type=req.type,
        payload=req.payload,
    )
    return {"status": "saved", "message_id": msg_id}
