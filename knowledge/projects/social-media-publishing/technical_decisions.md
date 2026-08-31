# Social Campaign Publisher — Technical Decisions

## Why an Adapter Pattern instead of direct API calls per platform
Scalability and maintainability. Every platform handles media uploads and
text limits differently (e.g. LinkedIn's multi-step image upload vs.
simpler standard endpoints). With the Adapter Pattern, the core campaign
engine doesn't need to know how LinkedIn specifically works — it just
calls a standardized `publish()` method. Adding a new platform later
means writing a new adapter, not touching the core logic.

## Why real LinkedIn but sandboxed everything else
The project's "sandbox-first" principle was intentionally overridden for
LinkedIn specifically, to demonstrate a fully functional, live API
integration rather than only simulated behavior — a deliberate choice to
prove out real OAuth, real token handling, and real publishing end to
end, while keeping the other platforms safe for local testing without
needing live developer credentials for all four.

## Why a human-in-the-loop review step instead of full automation
In production, AI output is unpredictable. Brands can't afford an LLM
hallucinating a controversial opinion or a broken link on their official
channels. The manual review step combines the speed of AI generation with
the safety of human oversight — treated as a mandatory architecture
choice for enterprise-facing generative AI, not an optional nice-to-have.

## Why idempotency keys and exponential backoff for publishing
To handle the risk of duplicate posts if an API call fails or times out.
If the system doesn't get a clear success response, it can safely retry
the request without risking spamming the user's feed with duplicate
posts.

## Why Alembic instead of `create_all`
Schema changes are managed exclusively through Alembic migrations going
forward, since `create_all` doesn't support controlled, reviewable,
incremental schema evolution the way a real production system needs —
though Alembic's autogenerate has its own gotchas (see `tradeoffs.md`).

## Why a dual-strategy content truncation approach
To control LLM token usage, source content is capped at a fixed character
limit. Rather than blindly cutting text at that limit, the system uses a
structure-aware "take from start" strategy for scraped web articles (where
the beginning usually carries the core content) and an even-sampling
strategy across the whole length for flat YouTube transcripts (where
important content can appear anywhere) — maximizing what the limited
context window is actually used for.
