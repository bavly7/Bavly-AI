# RULES.md — Bavly Project Rules

> Non-negotiable constraints. Any agent (Claude or otherwise) working on
> this project must follow these. If a request conflicts with a rule here,
> flag the conflict instead of silently violating it.

## Hallucination / Grounding Rules

1. Bavly must NEVER invent facts about the project owner. Every claim in a
   personal/project/certification answer must trace back to retrieved
   context (`knowledge_chunks`, `certifications`, or `projects` tables).
2. If retrieval confidence is below threshold, or no relevant chunk is
   found, the system MUST respond with an explicit "I don't have enough
   information about that" (localized to user's language) — never guess
   or extrapolate.
3. General knowledge questions (not about the owner) may be answered from
   the LLM's general knowledge, but must be clearly distinguishable from
   personal claims — never blend general knowledge into a personal answer
   in a way that implies it's owner-specific experience.
4. Every personal/project answer should be traceable to a `source_type`
   for potential citation display in the UI.
5. Do not remove or weaken the confidence-threshold / fallback logic to
   "make answers sound better" — a correct refusal beats a fabricated
   answer, always.

## Budget Rules

6. Every service/tool choice must be free-tier or self-hostable at $0
   unless explicitly approved otherwise by the owner.
7. If a free-tier limit is a real constraint (e.g., Supabase's 2-project
   cap), surface it and propose options — don't silently work around it
   in a way that risks data loss or surprise costs.
8. Before locking in any specific paid-adjacent service or one with
   changing free-tier terms, verify current terms rather than relying on
   possibly-stale training knowledge.

## Data Rules

9. Structured facts (certifications, tech stack, dates) go in structured
   tables, not embedded narrative chunks — don't blur this separation.
10. Manually-provided project narrative (why/how/challenges/lessons) is
    owner-supplied via structured interview, not auto-generated from
    GitHub content — never fabricate "why I built this" style content on
    the owner's behalf.
11. Any new project/certification data added must go through the same
    schema fields as existing entries — no ad hoc/inconsistent shapes.

## Build Process Rules

12. Follow the phase order in SPECS.md — do not skip ahead (e.g., don't
    add voice or animation before core RAG is validated on pilot data).
13. Each phase must be fully functional and deployed before starting the
    next, per SPECS.md §9.
14. When SPECS.md changes materially (schema, architecture, stack), update
    SPECS.md itself — don't let it drift out of sync with the real system.
15. Don't introduce LangGraph, MCP, or other framework complexity before
    the simpler linear version has been validated to work correctly.

## Language & Tone Rules

16. Respond in the language the user used (Egyptian Arabic colloquial, not
    MSA, for Arabic input; English for English input).
17. Tone/animation tags are generated as structured output, not left to
    the frontend to infer from raw text.

## Agent Collaboration Rules

18. Primary collaborator is Claude, but these files must be self-contained
    enough for any competent agent/dev to pick up the project correctly.
19. Check TASKS.md for current phase/status and open decisions before
    proposing new work — don't re-decide settled architecture questions
    without cause. Check BLOCK.md for any active unresolved struggle
    before starting new work in the same area.
20. When an agent hits an error, failed fetch, or ambiguous spec, log it
    in BLOCK.md immediately. Once resolved, delete the entry — don't let
    it accumulate as dead history.
21. When a rule here blocks a request, say so explicitly rather than
    quietly complying or quietly ignoring the instruction.