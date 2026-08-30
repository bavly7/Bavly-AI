# TASKS.md — Progress Tracker
 
> Tracks phase status, what's done, what's pending, and open decisions.
> Update at the end of every work session. This file persists — unlike
> BLOCK.md, entries here are not deleted when resolved, just marked done.
 
## Current Phase
**Phase 0 — Data foundation** (not yet started)
 
## Decided So Far
- Stack: Python backend, FastAPI, PostgreSQL + pgvector (Supabase, separate
  email/account), React frontend, LangGraph added in Phase 2.
- Data split: structured facts (tables) vs narrative (embedded chunks) vs
  derived GitHub content.
- Data collection approach: hybrid — pilot schema against 2 real projects
  before bulk-populating the rest.
- Build order: text-only RAG chatbot -> scale data -> LangGraph -> GitHub
  ingestion -> multilingual -> voice -> character/animation -> polish.
- Tools: plain Python/LangGraph tools first; MCP wrapper optional Phase 7
  capstone, not a core requirement.
- Repo convention: SPECS.md, RULES.md, TASKS.md, BLOCK.md live at repo
  root. Real, descriptive commit messages per meaningful change (not
  squash-at-the-end), e.g. `feat(phase1): linear RAG retrieval + generation
  working on pilot data`.
## Open Decisions (need answers before relevant phase starts)
- [ ] Which 2 projects are the pilot projects for Phase 0/1?
- [ ] LLM provider (free/rate-limited) — not yet chosen.
- [ ] Embedding model (multilingual, free) — not yet chosen.
- [ ] STT/TTS provider, especially Egyptian Arabic quality — not yet
      evaluated.
- [ ] Frontend + backend hosting providers — not yet chosen.
## Phase Checklist
 
### Phase 0 — Data foundation
- [ ] Finalize schema (already drafted in SPECS.md §3)
- [ ] Structured interview → pilot project #1
- [ ] Structured interview → pilot project #2
- [ ] Extract certifications + personal bio data
- [ ] Supabase project created (new account) + pgvector enabled
- [ ] Schema migrated, pilot data populated
### Phase 1 — Core RAG (text-only, linear, no graph)
- [ ] Embedding pipeline (chunk → embed → store)
- [ ] Retrieval function (vector search + structured lookup)
- [ ] Generation function (grounded answer + refusal fallback)
- [ ] Validate against pilot data (no hallucination, refusal works)
- [ ] FastAPI endpoint wrapping retrieval + generation
- [ ] Minimal frontend chat UI, deployed publicly
### Phase 2 — Scale data + LangGraph
- [ ] Remaining project interviews + bulk ingest
- [ ] Port linear RAG into LangGraph (intent routing, confidence gating)
- [ ] Conversation history/state (LangGraph checkpointer)
- [ ] Caching node
### Phase 3 — GitHub ingestion pipeline
- [ ] Webhook receiver
- [ ] Diff-based change detection
- [ ] Re-embedding + cache invalidation on update
### Phase 4 — Multilingual
- [ ] Language detection node
- [ ] Egyptian Arabic prompt tuning + testing
### Phase 5 — Voice
- [ ] STT integration
- [ ] TTS integration (language-aware)
### Phase 6 — Character/animation
- [ ] Tone-tagging node
- [ ] Frontend character + animation state mapping
### Phase 7 — Polish
- [ ] Monitoring/logging
- [ ] Rate limiting
- [ ] Security review
- [ ] (Optional) MCP wrapper over retrieval tools
## Notes / Context for Next Session
- Owner knows all project details well but wants structured extraction
  help to avoid missing details — fixed question set per project, applied
  consistently across all projects.
- Owner explicitly wants architecture/planning settled before code is
  written — don't jump ahead to code unprompted.
- Owner is being deliberate about commit hygiene on this project as a
  contrast to past habit of squash-publishing — treat commit granularity
  as part of the deliverable, not incidental.
 