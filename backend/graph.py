"""
Phase 2 — LangGraph orchestration

Ports the linear Phase 1 pipeline (retrieval.py + generation.py) into a
graph, per SPECS.md §4 and the Phase 2 architecture decisions:

  1. 100% LLM-based multi-intent router (no keyword matching) — replaces
     Phase 1's looks_like_certification_question()/looks_like_profile_link_
     question() keyword checks entirely. This is the deferred work noted
     in retrieval.py's docstring and in project memory: field/intent
     routing (certs, contacts/links, rag_content) now goes through a
     single structured-output LLM call instead of substring matching.
  2. Fan-out to specialized sub-nodes per extracted intent, fan-in to an
     aggregator, then a single generator synthesizes one unified answer.
  3. A downstream hallucination/completeness check runs BEFORE the answer
     reaches the user (RULES.md #1, #2, #5 — a refusal beats a
     fabrication, so on failure we fall back rather than ship an
     unverified claim).
  4. Conversation history reloaded from Postgres `messages` on every turn
     (Option A) — no in-memory session state, safe across Render
     free-tier cold starts.
  5. answer_cache checked first via cosine similarity; only high-
     confidence, non-fallback answers get cached, with a TTL.

Existing Phase 1 modules (retrieval.py, generation.py) are reused for
their underlying DB/vector primitives — this file does not re-implement
search_knowledge_chunks, get_certifications, embed_query, etc. What Phase 1
did in generation.py (single LLM call producing a full answer directly)
is superseded by this graph for any query that reaches it; generation.py
itself stays in place as the Phase 1 reference implementation but the
FastAPI endpoint should be pointed at run_graph() once this lands (see
NOTE at bottom of file).
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import END, START, StateGraph
from sqlalchemy import create_engine, text

from backend.retrieval import (
    RetrievedChunk,
    embed_query,
    get_certifications,
    search_knowledge_chunks,
    CONFIDENCE_THRESHOLD,
)

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
GROQ_API_KEY = os.environ["GROQ_API_KEY"]
ROUTER_MODEL = os.environ.get("ROUTER_MODEL", "openai/gpt-oss-120b")
GENERATOR_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
SECURITY_MODEL = os.environ.get("SECURITY_MODEL", "openai/gpt-oss-120b")

engine = create_engine(DATABASE_URL)
client = Groq(api_key=GROQ_API_KEY)

HISTORY_TURNS = 5  # ~5 turns = up to 10 messages, per spec
CACHE_SIMILARITY_THRESHOLD = 0.92  # near-duplicate query match, stricter than retrieval confidence
CACHE_TTL_HOURS = 24 * 7 # one week cache lifetime, per spec from its adv (data freshness , edge cases , database size)

# Same hardcoded, non-LLM-generated profile links as Phase 1 — a router
# intent can point here, but the URLs themselves are never LLM output.
PROFILE_LINKS = [
    {"platform": "LinkedIn", "url": "https://www.linkedin.com/in/bavly-waleed"},
    {"platform": "Kaggle", "url": "https://www.kaggle.com/bavlywaleed"},
    {"platform": "GitHub", "url": "https://github.com/bavly7"},
    {"platform": "Email", "url": "mailto:bavly.waleed777@gmail.com"},
    {"platform": "Phone", "url": "tel:+201200020385"},
]
FALLBACK_MESSAGES = {
    "ar": "معلش، مش لاقي معلومة كافية عن الموضوع ده حاليًا.",
    "en": "I don't have enough information about that yet.",
}


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def _merge_dict(left: dict, right: dict) -> dict:
    """Reducer for retrieved_data: sub-nodes run in parallel and each
    writes its own key, so a shallow merge is all that's needed — no two
    sub-nodes ever write the same key."""
    return {**left, **right}


class GraphState(TypedDict, total=False):
    session_id: str
    query: str
    language: str  # 'ar' | 'en'
    history: list[dict]  # [{"role": ..., "content": ...}, ...]

    # Router output
    intents: list[str]  # subset of 'rag_content' | 'certifications' | 'links'
    cert_domain: str | None
    project_name: str | None

    # Cache
    cache_hit: bool
    cache_answer: dict | None
    query_embedding: list[float]

    # Sub-node outputs, merged in parallel via _merge_dict
    retrieved_data: Annotated[dict, _merge_dict]

    # Generation
    answer: str
    sources: list[str]
    certificate_links: list[dict]
    profile_links: list[dict]
    confident: bool

    # Security check
    security_passed: bool
    security_retry_count: int


# ---------------------------------------------------------------------------
# History (Option A — reload from Postgres every turn)
# ---------------------------------------------------------------------------

def load_history(state: GraphState) -> dict:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT role, content FROM messages "
                "WHERE session_id = :session_id "
                "ORDER BY created_at DESC LIMIT :limit"
            ),
            {"session_id": state["session_id"], "limit": HISTORY_TURNS * 2},
        ).fetchall()
    history = [{"role": r.role, "content": r.content} for r in reversed(rows)]
    return {"history": history}


# ---------------------------------------------------------------------------
# Cache check (semantic, via query_embedding cosine similarity)
# ---------------------------------------------------------------------------

def check_cache(state: GraphState) -> dict:
    query_embedding = embed_query(state["query"])

    sql = text("""
        SELECT answer, sources, project_id_tags,
               1 - (query_embedding <=> :query_embedding) AS similarity
        FROM answer_cache
        WHERE expires_at > :now
        ORDER BY query_embedding <=> :query_embedding
        LIMIT 1
    """)
    with engine.connect() as conn:
        row = conn.execute(
            sql,
            {"query_embedding": str(query_embedding), "now": datetime.now(timezone.utc)},
        ).fetchone()

    if row and row.similarity >= CACHE_SIMILARITY_THRESHOLD:
        cached = json.loads(row.answer) if isinstance(row.answer, str) else row.answer
        return {
            "cache_hit": True,
            "cache_answer": cached,
            "query_embedding": query_embedding,
        }

    return {"cache_hit": False, "cache_answer": None, "query_embedding": query_embedding}


def route_after_cache(state: GraphState) -> Literal["cache_respond", "route_intents"]:
    return "cache_respond" if state.get("cache_hit") else "route_intents"


def cache_respond(state: GraphState) -> dict:
    """Serves the cached answer verbatim, skipping generation + security
    check entirely (it was already validated when first cached)."""
    cached = state["cache_answer"]
    return {
        "answer": cached["answer"],
        "sources": cached.get("sources", []),
        "certificate_links": cached.get("certificate_links", []),
        "profile_links": cached.get("profile_links", []),
        "confident": True,
        "security_passed": True,
    }


def write_cache(state: GraphState) -> dict:
    """Only high-confidence, non-fallback answers are cached (spec #5).
    A refusal/fallback or a security-check failure must never be cached,
    since caching it would repeat a wrong/unhelpful answer to every
    future near-duplicate query."""
    if state.get("cache_hit"):
        return {}  # already served from cache, nothing new to write
    if not state.get("confident") or not state.get("security_passed"):
        return {}

    payload = json.dumps({
        "answer": state["answer"],
        "sources": state.get("sources", []),
        "certificate_links": state.get("certificate_links", []),
        "profile_links": state.get("profile_links", []),
    })
    now = datetime.now(timezone.utc)
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO answer_cache "
                "(id, query_hash, query_embedding, answer, sources, project_id_tags, "
                " created_at, expires_at) "
                "VALUES (:id, :query_hash, :query_embedding, :answer, :sources, :tags, "
                " :created_at, :expires_at)"
            ),
            {
                "id": str(uuid.uuid4()),
                "query_hash": str(hash(state["query"])),
                "query_embedding": str(state["query_embedding"]),
                "answer": payload,
                "sources": state.get("sources", []),
                "tags": [],
                "created_at": now,
                "expires_at": now + timedelta(hours=CACHE_TTL_HOURS),
            },
        )
    return {}


# ---------------------------------------------------------------------------
# Router — single structured-output LLM call, multi-intent, no keywords
# ---------------------------------------------------------------------------

ROUTER_SYSTEM_PROMPT = """You are an intent router for an AI portfolio assistant \
(Bavly). Given a user message (Egyptian Arabic, English, mixed, with possible \
typos/colloquialisms), extract ALL intents present — a single message can and often \
does contain more than one.

Return ONLY a JSON object matching this schema, nothing else:
{
  "intents": ["rag_content" | "certifications" | "links"],
  "cert_domain": string or null,   // e.g. "computer vision", "machine learning" — \
only if intents includes "certifications" AND a specific domain was named; null for a \
general "show me your certifications" ask
  "project_name": string or null,  // named project if the user asked about one specifically
  "language": "ar" | "en"
}

Intent definitions:
- "rag_content": asking about background, experience, a project's details, skills, \
personal/general questions about the owner.
- "certifications": asking about certificates, courses, training, credentials.
- "links": asking for contact info, social/profile links (LinkedIn, GitHub, Kaggle), \
phone, email.

A message can have zero, one, or multiple intents. If the message is unrelated to the \
owner entirely (pure general knowledge, e.g. "what's the capital of France"), return \
intents: ["rag_content"] and let downstream confidence gating handle it."""


def route_intents(state: GraphState) -> dict:
    parsed = None

    try:
        response = client.chat.completions.create(
            model=ROUTER_MODEL,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": state["query"]},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"⚠️ Router failed with error: {e}")
        parsed = {
            "intents": ["rag_content"],
            "cert_domain": None,
            "project_name": None,
            "language": "en"
        }

    intents = [i for i in parsed.get("intents", []) if i in ("rag_content", "certifications", "links")]
    if not intents:
        intents = ["rag_content"]

    return {
        "intents": intents,
        "cert_domain": parsed.get("cert_domain"),
        "project_name": parsed.get("project_name"),
        "language": parsed.get("language", "en"),
    }

def dispatch_intents(state: GraphState) -> list[str]:
    """Conditional edge: fans out to every sub-node whose intent was
    extracted by the router. LangGraph runs these in parallel and joins
    at aggregate_context (the single common downstream node)."""
    node_map = {
        "rag_content": "rag_content_node",
        "certifications": "certifications_node",
        "links": "links_node",
    }
    return [node_map[i] for i in state["intents"] if i in node_map]


# ---------------------------------------------------------------------------
# Sub-nodes (parallel branches)
# ---------------------------------------------------------------------------

def rag_content_node(state: GraphState) -> dict:
    chunks = search_knowledge_chunks(state["query"])
    confident = bool(chunks) and chunks[0].similarity >= CONFIDENCE_THRESHOLD
    return {
        "retrieved_data": {
            "rag_chunks": chunks if confident else [],
            "rag_confident": confident,
        }
    }

def certifications_node(state: GraphState) -> dict:
    domain = state.get("cert_domain")
    certs = get_certifications(field_filter=domain)


    if not domain and len(certs) > 40:
        certs = certs[:40]

    return {"retrieved_data": {"certifications": certs}}


def links_node(state: GraphState) -> dict:
    return {"retrieved_data": {"profile_links": PROFILE_LINKS}}


# ---------------------------------------------------------------------------
# Aggregation + generation
# ---------------------------------------------------------------------------

def aggregate_context(state: GraphState) -> dict:
    """Join point for the parallel sub-nodes. No new retrieval happens
    here — purely reshapes what the sub-nodes already wrote into
    generation-ready fields."""
    data = state.get("retrieved_data", {})

    rag_chunks: list[RetrievedChunk] = data.get("rag_chunks", [])
    rag_confident: bool = data.get("rag_confident", False)
    certifications: list[dict] = data.get("certifications", [])
    profile_links: list[dict] = data.get("profile_links", [])

    certificate_links = [
        {"title": c["title"], "issuer": c["issuer"], "url": c["file_url"]}
        for c in certifications
    ]

    overall_confident = rag_confident or bool(certificate_links) or bool(profile_links)

    return {
        "certificate_links": certificate_links,
        "profile_links": profile_links,
        "confident": overall_confident,
        # stash chunks temporarily for the generator; not part of the
        # public GraphState contract returned to the API layer
        "retrieved_data": {"rag_chunks_final": rag_chunks},
    }


def _format_context(chunks: list[RetrievedChunk]) -> str:
    lines = [f"[{i}] (source_type={c.source_type}) {c.content}" for i, c in enumerate(chunks, start=1)]
    return "\n".join(lines) if lines else "(no additional context retrieved)"


def _format_history(history: list[dict]) -> str:
    if not history:
        return "(no prior messages)"
    return "\n".join(f"{m['role']}: {m['content']}" for m in history)


def generate_answer(state: GraphState) -> dict:
    language = state.get("language", "en")

    if not state["confident"]:
        return {
            "answer": FALLBACK_MESSAGES[language],
            "sources": [],
        }

    chunks = state.get("retrieved_data", {}).get("rag_chunks_final", [])
    context = _format_context(chunks)

    cert_text = ""
    if state.get("certificate_links"):
        cert_text = "\nCERTIFICATIONS FOUND IN DATABASE:\n" + "\n".join(
            f"- {c['title']} by {c['issuer']}" for c in state["certificate_links"]
        )

    profile_text = ""
    if state.get("profile_links"):
        profile_text = "\nOWNER PROFILES:\n" + "\n".join(
            f"- {p['platform']}: {p['url']}" for p in state["profile_links"]
        )

    lang_instruction = (
        "Respond in Egyptian Arabic colloquial (not Modern Standard Arabic)."
        if language == "ar" else "Respond in English."
    )
    system_prompt = (
        "You ARE Bavly Waleed — a Computer Vision & AI engineer. You're chatting with "
        "a recruiter or visitor about your own background, projects, and experience.\n\n"
        "PERSONALITY & TONE:\n"
        "- Be warm, friendly, and conversational (ودود، مرحب، ودمك خفيف).\n"
        "- Use emojis naturally and tastefully (حط إيموجيز بشكل لطيف).\n"
        "- Speak in FIRST PERSON ('I', 'my', 'me') — you ARE Bavly, not an assistant talking about him.\n"
        "- Match the user's language: Egyptian Arabic → reply in Egyptian Arabic; English → English.\n\n"
        "GROUNDING RULES:\n"
        "- Only state facts that are in CONTEXT, CERTIFICATIONS, or PROFILES.\n"
        "- If something isn't in your data, say so directly and briefly — don't over-explain.\n"
        "- Never invent projects, roles, or experiences not in the context.\n"
        "- Do not include raw URLs in your text — links are handled separately.\n\n"
        "SMART FILTERING:\n"
        "- If the user asks about something specific (e.g., 'Exology'), and it's not in your data, "
        "briefly say you don't have info about that specific thing, then pivot to what you DO have "
        "that's related (e.g., 'but here's my experience at FlyRank...').\n"
        "- Connect the conversation to your portfolio naturally — be helpful, not sales-y.\n\n"
        "CLOSING:\n"
        "- End with a short, friendly follow-up or offer to share more (e.g., 'Want me to show you the code?' or 'حب أقولك أكتر عن المشروع ده؟').\n"
        "- Keep it casual and genuine — like you're talking to a colleague, not pitching.\n\n"
        f"- {lang_instruction}"
    )
    user_prompt = (
        f"CONVERSATION HISTORY:\n{_format_history(state.get('history', []))}\n\n"
        f"CONTEXT:\n{context}{cert_text}{profile_text}\n\n"
        f"QUESTION:\n{state['query']}"
    )

    response = client.chat.completions.create(
        model=GENERATOR_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
    )
    answer = response.choices[0].message.content.strip()
    sources = sorted({c.source_type for c in chunks})

    return {"answer": answer, "sources": sources}


# ---------------------------------------------------------------------------
# Security / hallucination check node
# ---------------------------------------------------------------------------

SECURITY_SYSTEM_PROMPT = """You are a strict fact-checking auditor. You are given the \
CONTEXT that was available to an assistant, the USER'S QUESTION, and the assistant's \
DRAFT ANSWER. Verify:

1. Every factual claim in DRAFT ANSWER is directly supported by CONTEXT (no invented \
facts, dates, names, or numbers not present in CONTEXT).
2. If the user's question had multiple parts/intents, DRAFT ANSWER addresses all of them \
(or explicitly says it doesn't have info for the ones it can't answer).

Return ONLY a JSON object: {"passed": true|false, "reason": string}"""


def security_check(state: GraphState) -> dict:
    # Cached and fallback answers are pre-validated / inherently safe —
    # skip the extra LLM call.
    if state.get("cache_hit") or not state.get("confident"):
        return {"security_passed": True}

    chunks = state.get("retrieved_data", {}).get("rag_chunks_final", [])
    context = _format_context(chunks)
    cert_text = "\n".join(f"- {c['title']}" for c in state.get("certificate_links", []))
    profile_text = "\n".join(f"- {p['platform']}: {p['url']}" for p in state.get("profile_links", []))

    audit_prompt = (
        f"CONTEXT:\n{context}\nCERTIFICATIONS:\n{cert_text}\nPROFILES:\n{profile_text}\n\n"
        f"USER'S QUESTION:\n{state['query']}\n\n"
        f"DRAFT ANSWER:\n{state['answer']}"
    )

    response = client.chat.completions.create(
        model=SECURITY_MODEL,
        messages=[
            {"role": "system", "content": SECURITY_SYSTEM_PROMPT},
            {"role": "user", "content": audit_prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    try:
        result = json.loads(response.choices[0].message.content)
        passed = bool(result.get("passed", False))
    except (json.JSONDecodeError, TypeError):
        # Audit itself failed to parse — treat as a failure, not a pass.
        # Never let a malformed check silently wave a claim through.
        passed = False

    return {"security_passed": passed}


def route_after_security(state: GraphState) -> Literal["write_cache_node", "security_fallback"]:
    if state.get("security_passed"):
        return "write_cache_node"
    retry_count = state.get("security_retry_count", 0)
    return "write_cache_node" if retry_count >= 1 else "security_fallback"


def security_fallback(state: GraphState) -> dict:
    """One retry attempt: if the audit fails once, don't ship the
    unverified answer — regenerate once more. If it fails again, RULES.md
    #5 wins: refuse rather than risk a fabrication reaching the user."""
    retry_count = state.get("security_retry_count", 0) + 1
    if retry_count >= 2:
        language = state.get("language", "en")
        return {
            "answer": FALLBACK_MESSAGES[language],
            "confident": False,
            "security_passed": True,  # a fallback message is trivially safe
            "security_retry_count": retry_count,
        }
    return {"security_retry_count": retry_count}


# ---------------------------------------------------------------------------
# Graph compilation
# ---------------------------------------------------------------------------

def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("load_history", load_history)
    graph.add_node("check_cache", check_cache)
    graph.add_node("cache_respond", cache_respond)
    graph.add_node("route_intents", route_intents)
    graph.add_node("rag_content_node", rag_content_node)
    graph.add_node("certifications_node", certifications_node)
    graph.add_node("links_node", links_node)
    graph.add_node("aggregate_context", aggregate_context)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("security_check", security_check)
    graph.add_node("security_fallback", security_fallback)
    graph.add_node("write_cache_node", write_cache)

    graph.add_edge(START, "load_history")
    graph.add_edge("load_history", "check_cache")
    graph.add_conditional_edges("check_cache", route_after_cache, ["cache_respond", "route_intents"])
    graph.add_edge("cache_respond", END)

    graph.add_conditional_edges(
        "route_intents", dispatch_intents,
        ["rag_content_node", "certifications_node", "links_node"],
    )
    graph.add_edge("rag_content_node", "aggregate_context")
    graph.add_edge("certifications_node", "aggregate_context")
    graph.add_edge("links_node", "aggregate_context")

    graph.add_edge("aggregate_context", "generate_answer")
    graph.add_edge("generate_answer", "security_check")
    graph.add_conditional_edges(
        "security_check", route_after_security, ["write_cache_node", "security_fallback"],
    )
    # Retry loop: a failed audit regenerates once, then re-audits.
    graph.add_edge("security_fallback", "generate_answer")
    graph.add_edge("write_cache_node", END)

    return graph.compile()


_compiled_graph = None


def run_graph(session_id: str, query: str) -> dict:
    """Public entrypoint — mirrors generation.generate()'s return shape
    so the FastAPI layer's response model doesn't need to change."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()

    final_state = _compiled_graph.invoke({
        "session_id": session_id,
        "query": query,
        "security_retry_count": 0,
    })

    return {
        "answer": final_state["answer"],
        "sources": final_state.get("sources", []),
        "certificate_links": final_state.get("certificate_links", []),
        "profile_links": final_state.get("profile_links", []),
    }


# NOTE: main.py's /chat route currently calls generation.generate(message).
# Swapping to Phase 2 means changing that one call site to:
#     result = run_graph(session_id, message)
# No other change needed — ChatResponse's shape is unchanged. Left as an
# explicit manual step rather than done here, since RULES.md #13 requires
# Phase 2 to be validated before Phase 1's linear path is retired.