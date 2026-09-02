"""
Phase 1 — FastAPI endpoint

Thin HTTP wrapper around generation.generate(), which itself wraps
retrieval.retrieve(). No new logic lives here — this file's only job is
transport (HTTP in, JSON out) plus session/message persistence into the
`sessions` / `messages` tables from SPECS.md §3.

RULES.md notes respected here:
  - #4: every answer stays traceable to sources (passed straight through
    from generation.generate(), not altered).
  - #12/#15: no LangGraph, no intent classifier, no extra framework layer
    — Phase 1 stays linear, per SPECS.md build order.
  - #16: language handling is entirely generation.py's responsibility;
    this file does not re-detect or override language.

Not implemented here (intentionally, out of Phase 1 scope):
  - check_cache / write_cache (answer_cache table) — Phase 2, LangGraph
    node per SPECS.md §4.
  - tone_tag — Phase 6.
  - STT/TTS endpoints — Phase 5.
"""

import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from backend.generation import generate
from backend.retrieval import RetrievedChunk

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
# Comma-separated list of allowed frontend origins, e.g.
# "https://bavly-portfolio.vercel.app,http://localhost:5173"
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")

engine = create_engine(DATABASE_URL)

app = FastAPI(title="Bavly Chat API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # if omitted, a new session is created


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[str]
    certificate_links: list[dict]
    profile_links: list[dict]


# ---------------------------------------------------------------------------
# Session / message persistence (SPECS.md §3 `sessions` / `messages`)
# ---------------------------------------------------------------------------

def _ensure_session(session_id: str | None) -> str:
    """Returns a valid session_id, creating a new session row if needed,
    and touching last_active if it already exists."""
    with engine.begin() as conn:
        if session_id:
            row = conn.execute(
                text("SELECT id FROM sessions WHERE id = :id"),
                {"id": session_id},
            ).fetchone()
            if row:
                conn.execute(
                    text("UPDATE sessions SET last_active = :now WHERE id = :id"),
                    {"now": datetime.now(timezone.utc), "id": session_id},
                )
                return session_id
            # A session_id was supplied but doesn't exist — fall through
            # and create a fresh one rather than silently erroring, since
            # the frontend may just be replaying a stale/local id.

        new_id = str(uuid.uuid4())
        conn.execute(
            text(
                "INSERT INTO sessions (id, created_at, last_active) "
                "VALUES (:id, :now, :now)"
            ),
            {"id": new_id, "now": datetime.now(timezone.utc)},
        )
        return new_id


def _save_message(session_id: str, role: str, content: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO messages (id, session_id, role, content, created_at) "
                "VALUES (:id, :session_id, :role, :content, :now)"
            ),
            {
                "id": str(uuid.uuid4()),
                "session_id": session_id,
                "role": role,
                "content": content,
                "now": datetime.now(timezone.utc),
            },
        )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="message must not be empty")

    session_id = _ensure_session(req.session_id)

    _save_message(session_id, "user", message)

    try:
        result = generate(message)
    except Exception as e:
        # Don't let a Groq/Cohere/DB hiccup surface as a raw 500 with a
        # stack trace to the recruiter-facing frontend.
        raise HTTPException(status_code=502, detail=f"generation failed: {e}")

    _save_message(session_id, "assistant", result["answer"])

    return ChatResponse(
        session_id=session_id,
        answer=result["answer"],
        sources=result["sources"],
        certificate_links=result["certificate_links"],
        profile_links=result["profile_links"],
    )


@app.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    """Lets the frontend rehydrate a conversation on page reload."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT role, content, created_at FROM messages "
                "WHERE session_id = :session_id ORDER BY created_at ASC"
            ),
            {"session_id": session_id},
        ).fetchall()

    return [
        {"role": r.role, "content": r.content, "created_at": r.created_at.isoformat()}
        for r in rows
    ]