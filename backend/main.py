"""
Phase 1-3 — FastAPI Backend

Main application entry point. Handles:
  - Phase 1/2: Chat endpoint with LangGraph RAG orchestration
  - Phase 3: GitHub webhook receiver for knowledge base auto-updates

RULES.md notes respected here:
  - #4: every answer stays traceable to sources (passed straight through
    from generation.generate(), not altered).
  - #16: language handling is entirely generation.py's responsibility;
    this file does not re-detect or override language.

Phases implemented:
  - Phase 1: Linear RAG (retrieval + generation)
  - Phase 2: LangGraph orchestration (routing, caching, security)
  - Phase 3: GitHub webhook ingestion (diff-based re-embedding)
"""

import os
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from backend.generation import generate
from backend.retrieval import RetrievedChunk

from backend.graph import run_graph
from backend.webhook import handle_github_webhook
from backend.ingestion import process_webhook_changes

import traceback

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
async def chat_endpoint(request: ChatRequest):
    try:
        
        active_session_id = _ensure_session(request.session_id)

        _save_message(active_session_id, "user", request.message)


        result = run_graph(
            session_id=active_session_id,
            query=request.message
        )

        
        _save_message(active_session_id, "assistant", result["answer"])

        return ChatResponse(
            session_id=active_session_id,  
            answer=result["answer"],
            sources=result.get("sources", []),
            certificate_links=result.get("certificate_links", []),
            profile_links=result.get("profile_links", []),
        )
    except Exception as e:
        print("🔥 ERROR IN /chat:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

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


# ---------------------------------------------------------------------------
# Phase 3 — GitHub Webhook Endpoint
# ---------------------------------------------------------------------------

@app.post("/webhook/github")
async def github_webhook_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(None)
):
    """
    Receives GitHub push webhooks and processes knowledge base updates.

    Signature verification happens in webhook.py. Changes are processed
    in the background to avoid webhook timeouts (GitHub expects <10s response).
    """
    try:
        # Parse and validate webhook (returns immediately)
        result = await handle_github_webhook(request, x_hub_signature_256)

        # If changes detected, queue background processing
        if result["status"] == "queued":
            changes = result["changes"]
            background_tasks.add_task(process_webhook_changes, changes)
            print(f"✅ Queued {len(changes)} file change(s) for processing")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print("🔥 ERROR IN /webhook/github:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))