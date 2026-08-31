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

## Open Decisions — RESOLVED
- [x] Repo name: `bavly`
- [x] Supabase: separate email/account dedicated to this project.
- [x] Projects in scope (3 total): `flyrank-capstone-social-studio`,
      `Automated-KYC-Onboarding-System-Egyptian-National-ID`,
      `Agentic-RAG-Retail-Assistant`. Pilot pair for Phase 0/1: KYC +
      Agentic RAG (richer architecture/trade-off stories). FlyRank added
      right after as the first scale-up project (Phase 2 start), not part
      of the original pilot validation.
- [x] LLM provider: Groq, model `openai/gpt-oss-120b`, key in `.env` as
      `GROQ_API_KEY`. OpenAI-compatible endpoint. NOTE: free tier is rate
      limited (~30 req/min, ~200K tokens/day as of research date) — design
      for graceful degradation (friendly rate-limit message), not silent
      failure, if the demo gets a traffic spike.
- [x] Embedding model: `CohereLabs/Cohere-embed-multilingual-v3.0`
      (candidate — confirm actual free access path, e.g. via Cohere API
      free tier or HF Inference, before Phase 0 implementation).
- [x] STT: Groq Whisper-large-v3 API.
- [x] TTS: `en-US-GuyNeural` (English), `ar-EG-ShakirNeural` (Egyptian
      Arabic) — Edge TTS voices. Confirm library/access path (e.g.
      `edge-tts` Python package) at Phase 5 implementation time.
- [x] Frontend hosting: Vercel.
- [x] Backend hosting: Render.

## Notes on Resolved Decisions
- Groq, Cohere, Edge TTS specifics (exact free-tier limits, access
  methods) should be re-verified live at the point of implementation for
  each phase — terms shift, and locking the *choice* now doesn't mean
  skipping a final check before writing the integration code.

## Phase Checklist

### Phase 0 — Data foundation
- [x] `knowledge/` folder structure established: `personal/`,
      `experience/{elevvo,nti,depi,flyrank,tips-hindawy,dhub-ai-agents}/`,
      `certifications/`, `projects/{kyc-onboarding,agentic-rag-retail,
      social-media-publishing}/` — each with per-topic .md files mapping
      to `knowledge_chunks` source_type + tags at ingestion time.
- [x] `personal/` complete: bio.md, education.md, skills.md, goals.md
- [~] `experience/` — 6 of 7 folders created (7th, D-Hub RPA Automation,
      held back until it actually starts — see note below).
      - [x] elevvo — complete (overview, responsibilities, achievements,
            learnings all filled)
      - [x] nti — complete (overview, responsibilities, achievements,
            learnings all filled)
      - [x] depi — complete (overview, responsibilities, achievements,
            learnings all filled)
      - [x] flyrank — complete (overview, responsibilities incl. scoped
            blockchain-intro note, achievements, learnings all filled)
      - [~] tips-hindawy — overview.md complete (IN PROGRESS, started
            8/29/2026, no end date yet); responsibilities.md still
            placeholder (fill once further along); no
            achievements.md/learnings.md yet (premature while in
            progress)
      - [~] dhub-ai-agents — overview.md complete (IN PROGRESS, started
            8/26/2026, no end date yet); responsibilities.md still
            placeholder; no achievements/learnings yet
      - [ ] dhub-rpa-automation — NOT YET CREATED. Starts next week per
            owner. Add once it actually begins.
- [ ] Finalize schema (already drafted in SPECS.md §3) — needs
      `experience` source_type added, and `file_url` column added to
      `certifications` table (see SPECS.md update needed)
- [x] Structured interview → pilot project #1 (KYC Onboarding System) —
      COMPLETE. All 10 files built: overview, motivation, problem,
      architecture, technical_decisions, challenges, tradeoffs,
      improvements, learnings, recruiter_qa, github_metadata.
- [x] Structured interview → pilot project #2 (Agentic RAG Retail
      Assistant) — COMPLETE. All 10 files built.
- [x] **Both pilot projects for Phase 0/1 now complete** (KYC +
      Agentic RAG). Schema validated against two real, rich projects —
      ready to move to Supabase setup / embedding pipeline in Phase 1,
      or continue gathering the remaining 2 projects (Social Campaign
      Publisher, PulseFit) first before implementation. Owner's call on
      order.
- [x] Structured interview → Social Campaign Publisher
      (= flyrank-capstone-social-studio, confirmed same repo) — COMPLETE.
      All 10 files built.
- [x] Structured interview → PulseFit — COMPLETE. All 10 files built.
      Note: `learnings.md` has 2 optional bonus questions unanswered
      (proudest moment, unlimited-resources wish) — not blocking.

## ALL 4 PROJECTS DATA COLLECTION COMPLETE
KYC Onboarding, Agentic RAG Retail, Social Campaign Publisher, PulseFit —
each with full 10-file knowledge sets (overview, motivation, problem,
architecture, technical_decisions, challenges, tradeoffs, improvements,
learnings, recruiter_qa, github_metadata). Phase 0 data foundation is
essentially done pending: Supabase setup, certifications file_url
mapping, and the one open CIB certificate question.
- [x] Certifications table finalized — 38 files inventoried and mapped to
      title/issuer/field (see chat history for full mapping). "AI For
      Everyone" confirmed via web search: Andrew Ng / DeepLearning.AI,
      field = AI Fundamentals. ONE remaining open item: "Bavly Waleed
      (CIB).pdf" — context/issuer still unknown, owner to confirm (cannot
      fetch Google Drive links directly — no auth access).
- [ ] Owner uploading all 38 cert files directly to Supabase Storage once
      bucket exists; `file_url` mapping finalized against exact storage
      paths at that point.
- [ ] Supabase project created (new account) + pgvector enabled
- [ ] Supabase Storage bucket set up for certification PDFs
- [ ] Schema migrated, pilot data populated
- [ ] (Phase 2 start) Structured interview → FlyRank/Social Media
      Publishing project narrative (distinct from the `experience/flyrank/`
      files, which cover the internship itself)
- [ ] (Deferred, post-build) Structured interview → **Bavly AI itself**
      as project #4 — the system's own build story (architecture,
      challenges, decisions, learnings). Deliberately done LAST, after
      the system is actually built, so answers reflect real lived
      experience rather than a plan. Handled as a special-cased/routed
      answer in the intent classifier rather than a normal retrieved
      chunk, to avoid the self-referential "chatbot describing itself
      via its own retrieval" complexity — same knowledge/projects/
      folder structure, just flagged.

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
