"""Web API for the service desk assistant. Start it with:  uvicorn api:app --reload"""
import os
import uuid

from anthropic import APIError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import tickets
from ask import answer

load_dotenv()
if not os.getenv("ANTHROPIC_API_KEY"):
    raise RuntimeError("ANTHROPIC_API_KEY is missing. Check your .env file.")

app = FastAPI(title="Service Desk Assistant", version="0.1.0")

# One conversation history per session. Kept in memory, so it resets when the server restarts.
sessions = {}
MAX_SESSIONS = 100


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    session_id: str | None = Field(default=None, description="Send this back to continue a conversation")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    sources: list[str]


@app.get("/health")
def health():
    """Used to check that the server is running."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Send one employee message and get the assistant's reply."""
    session_id = request.session_id or str(uuid.uuid4())
    if session_id not in sessions and len(sessions) >= MAX_SESSIONS:
        raise HTTPException(status_code=429, detail="Too many active sessions. Try again later.")

    history = sessions.setdefault(session_id, [])
    length_before = len(history)
    try:
        reply, sources = answer(request.message, history)
    except APIError:
        del history[length_before:]  # drop the half-finished turn so the next message works
        raise HTTPException(status_code=502, detail="The AI service is unavailable. Please try again.")
    return ChatResponse(session_id=session_id, reply=reply, sources=sources)


@app.get("/tickets/{ticket_id}")
def read_ticket(ticket_id: int):
    """Look up a ticket directly, without going through the AI."""
    ticket = tickets.get_ticket(ticket_id)
    if "error" in ticket:
        raise HTTPException(status_code=404, detail=ticket["error"])
    return ticket