# apps/api/routers/agents.py
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from database import get_db
from dependencies import get_current_user
from models import User, UserRole
from supervisor_agent import build_supervisor_agent

router = APIRouter(prefix="/agents", tags=["agents"])

APP_NAME = "attachiq_supervisor"

# Created once at import time and reused across every request, so that
# conversation history survives between a supervisor's messages.
session_service = InMemorySessionService()

# Tracks each supervisor's active ADK Session object directly, keyed by user_id.
# We hold the object ourselves rather than looking it up via
# session_service.get_session() — that lookup was silently missing and
# creating a fresh session on every call, wiping conversation history.
# MVP tradeoff: one supervisor can only have one active assessment
# conversation at a time. Lost on server restart, same as before.
active_sessions: dict[str, "object"] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/chat")
async def chat_with_agent(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.SUPERVISOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only supervisors can use this agent.",
        )

    user_id = str(current_user.id)

    # Reuse this supervisor's in-memory session if we have one and it matches
    # what the client sent; otherwise start a new conversation.
    session = active_sessions.get(user_id)
    if session is None or (request.session_id and session.id != request.session_id):
        session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)
        active_sessions[user_id] = session

    agent = build_supervisor_agent(db)
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    message = types.Content(role="user", parts=[types.Part(text=request.message)])

    async def event_stream():
        yield f"data: {json.dumps({'type': 'session', 'session_id': session.id})}\n\n"
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=message,
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        text = event.content.parts[0].text
                        yield f"data: {json.dumps({'type': 'done', 'content': text})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'error', 'content': 'No response content — the model call may have failed.'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Something went wrong talking to the model ({type(e).__name__}).'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")