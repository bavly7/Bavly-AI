# SPECS.md — Bavly Project Specification

> Source of truth for architecture, data model, and tech decisions.
> If behavior conflicts with this file, this file wins unless explicitly updated.

## 1. Project Summary

Bavly is an interactive AI portfolio: a chatbot character representing [Owner],
answering recruiter questions about background, certifications, skills, and
projects. Grounded in a personal knowledge base (RAG), multilingual
(Egyptian Arabic / English), with optional voice I/O and reactive character
animation. Deployed publicly at $0 budget.

## 2. Tech Stack

| Layer               | Choice                          | Notes |
|----------------------|----------------------------------|-------|
| Backend language      | Python                          | LangGraph, embeddings, STT/TTS libs all Python-first |
| Orchestration          | LangGraph                       | Added in Phase 2, after linear RAG is validated |
| Backend API             | FastAPI                        | REST/WebSocket endpoints |
| Database                 | PostgreSQL (Supabase, pgvector) | One DB for structured + vector data |
| Frontend                  | React / TS                     | Chat UI, character, voice recording |
| Hosting (backend)          | TBD — free tier, decide at deploy stage |
| Hosting (frontend)           | TBD — free tier, decide at deploy stage |
| STT/TTS                       | TBD — free option, evaluate Arabic dialect quality before locking in |
| Embeddings                     | TBD — multilingual model, free/self-hostable |
| LLM                              | TBD — free/rate-limited tier, swappable via abstraction layer |

**Note:** "TBD" items are intentionally left open until the deployment stage,
since free-tier terms/limits change over time. Verify current terms before
committing, don't rely on stale info.

## 3. Data Model (PostgreSQL + pgvector)

```sql
-- Structured facts
certifications (
  id, title, issuer, date, skills TEXT[], url, description
)

projects (
  id, name, github_repo, tech_stack TEXT[],
  start_date, end_date, summary
)

-- Narrative / RAG-searchable chunks
knowledge_chunks (
  id,
  source_type,        -- 'personal_bio' | 'project_narrative' | 'github_readme' | 'certification'
  project_id,          -- nullable FK -> projects
  content,              -- raw text chunk
  embedding VECTOR(N),   -- pgvector column, N = embedding model dim
  language,               -- 'ar-EG' | 'en' | 'auto'
  created_at, updated_at
)

-- Conversation memory
sessions (id, created_at, last_active)
messages (id, session_id, role, content, tone_tag, created_at)

-- Cache
answer_cache (
  id, query_hash, query_embedding VECTOR(N),
  answer, sources TEXT[], project_id_tags TEXT[],
  created_at, expires_at
)
```

Design principle: **facts vs narrative are stored separately.**
Facts (certifications, tech stack, dates) = structured lookup, near-zero
hallucination risk. Narrative (why/how/challenges/lessons) = embedded chunks,
retrieved via similarity search, always must cite source.

## 4. RAG / Graph Flow (LangGraph, Phase 2+)

```
START
 → detect_language
 → check_cache            (semantic match on query_embedding; hit -> respond)
 → classify_intent        (personal | certification | project | technical | general)
 → route_source           (conditional edge)
     → retrieve_structured   (certifications/projects tables)
     → retrieve_project_kb   (vector search, knowledge_chunks)
     → retrieve_personal     (vector search, personal_bio chunks)
 → check_confidence       (below threshold -> fallback_response)
 → generate_answer        (context-grounded, includes conversation history)
 → validate_answer        (optional: check claims against retrieved context)
 → tag_tone                (structured output: {tone: "humorous"|"serious"|...})
 → respond                 (save to messages, write cache, return to frontend)

fallback_response -> respond   (localized "I don't have enough info" message)
```

State object carries: `messages`, `language`, `intent`, `retrieved_chunks`,
`confidence`, `answer`, `tone`, `sources`.

Phase 1 (before LangGraph) implements this same logic linearly in plain
Python, without the graph library, to validate RAG quality first.

## 5. GitHub Ingestion Pipeline

```
GitHub push webhook
 → identify changed files (from webhook payload diff)
 → re-parse only changed files (README, structure, etc.)
 → extract relevant info -> update knowledge_chunks for that project
 → re-embed changed chunks only
 → invalidate answer_cache entries tagged with that project_id
 → ready
```

Fallback: scheduled daily job as a safety net if webhook delivery fails.
Manually-provided project metadata (why built, decisions, challenges,
trade-offs, lessons) is NOT auto-extracted from GitHub — supplied via the
structured interview process and stored directly in `knowledge_chunks`
with `source_type = 'project_narrative'`.

## 6. Multilingual Handling

- Detect language from input (text or STT output metadata).
- Embeddings: multilingual model, single knowledge base (not duplicated
  per language) — retrieval works across languages via multilingual
  embedding space.
- Generation: explicit prompt instruction to respond in Egyptian Arabic
  dialect (not MSA) when input is Arabic; English otherwise.

## 7. Voice & Animation

- STT converts input audio -> text -> normal pipeline.
- TTS converts final answer -> audio, language-aware.
- Tone tagging (`tag_tone` node) outputs a structured intent label
  alongside the answer. Frontend maps tone label -> animation state.
  Animation logic is deterministic and decoupled from generation — the
  LLM never directly controls animation, only emits a tag.

## 8. Certification Display (Structured, not inline)

When `get_certifications()` retrieval fires, the response object carries a
separate structured field alongside the natural-language answer:

```json
{
  "answer": "Yes — I have a Computer Vision Engineer certification from ITI Mahara Tech...",
  "tone": "informative",
  "certificate_links": [
    {"title": "Computer Vision Engineer", "issuer": "ITI Mahara Tech", "url": "<supabase_storage_url>"}
  ]
}
```

Generation never embeds a raw URL in the prose text. The frontend renders
`certificate_links` as clickable cards/chips below the chat message
(same UI pattern as source citations). This keeps certificate PDFs
genuinely retrievable by the recruiter, not just described.

## 9. Tools (callable functions / LangGraph tools)

- `search_project_kb(query, project_id?)`
- `search_personal_kb(query)`
- `get_certifications(filter?)`
- `get_project_metadata(project_id)`
- `fetch_repo_structure(repo)`
- `fetch_readme(repo)`
- `fetch_commit_history(repo, since?)`   — ingestion pipeline only
- `detect_language(text)`
- `check_cache(query_hash)` / `write_cache(query_hash, answer)`
- `classify_intent(query)`
- `validate_answer(answer, context)`
- `speech_to_text(audio)` — Phase 5
- `text_to_speech(text, language, voice?)` — Phase 5

Implemented as plain Python functions / LangGraph tools first (single
consumer = this app). MCP wrapper over retrieval tools is an optional
Phase 7 capstone feature, not a functional requirement.

## 11. Project Interview Question Set

Standard question set used to build each project's `knowledge/projects/{name}/`
folder (10 core files + 2 optional bonus questions folded into
`learnings.md`). Applied consistently across all projects, including the
deferred Bavly AI self-referential project, for retrieval consistency.

1. Motivation — why this project specifically?
2. Hardest challenge, as a story — not a list of bugs, but what it was
   actually like to hit and solve the hardest problem.
3. Personal learning — what changed in how the owner approaches problems,
   not just a technical skill list.
4. Recruiter Q&A — anticipated questions not obvious from the README.
5. *(Optional, added after PulseFit)* Proudest moment/detail — something
   the owner is personally proud of that a recruiter might not think to
   ask about directly.
6. *(Optional, added after PulseFit)* If given unlimited time/resources,
   what's the one thing they'd add or change first?

Everything else (overview, problem, architecture, technical_decisions,
tradeoffs, improvements, github_metadata) is drafted directly from the
project's README/documentation and doesn't require a live interview
question, since READMEs already cover it well when they're detailed.

## 12. Build Phases

0. Data foundation (schema + pilot project extraction)
1. Core RAG, text-only, linear (no graph), 2 pilot projects, deployed
2. Scale data + port to LangGraph (routing, state, caching)
3. GitHub ingestion pipeline
4. Multilingual
5. Voice I/O
6. Character/animation
7. Polish (monitoring, rate limiting, security, optional MCP)

Each phase must be fully functional and deployed before starting the next.
