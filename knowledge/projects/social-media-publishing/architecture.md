# Social Campaign Publisher — Architecture

```
                          ┌─────────────────────────┐
                          │        Frontend          │
                          │  create.html (dashboard) │
                          └────────────┬─────────────┘
                                       │ multipart/form-data
                                       ▼
                          ┌─────────────────────────┐
                          │      FastAPI App          │
                          │        (main.py)          │
                          └────────────┬─────────────┘
                                       │
                 ┌─────────────────────┼─────────────────────┐
                 ▼                     ▼                     ▼
        ┌────────────────┐   ┌──────────────────┐   ┌────────────────┐
        │  routers/       │   │  routers/          │   │  routers/       │
        │  campaigns.py   │   │  webhooks.py       │   │  sandbox.py     │
        │ (create + POST) │   │ (publish confirms) │   │ (fake platform  │
        └────────┬────────┘   └──────────┬─────────┘   │   endpoints)    │
                 │                       │              └────────────────┘
                 ▼                       │
      ┌──────────────────────┐          │
      │  caption_service.py  │          │
      │  (Groq / LLM prompt) │          │
      └──────────┬───────────┘          │
                 │                       │
                 ▼                       │
      ┌──────────────────────┐          │
      │     database.py       │◄─────────┘
      │  (SQLAlchemy async,   │
      │   Supabase Postgres)  │
      └──────────┬───────────┘
                 │
                 ▼
      ┌──────────────────────┐        ┌───────────────────────┐
      │  scheduler.py         │───────▶│  worker.py             │
      │  (APScheduler,        │        │  (publish_social_      │
      │   SQLAlchemy jobstore)│        │   post_job)             │
      └──────────────────────┘        └───────────┬────────────┘
                                                    │
                                    ┌───────────────┼────────────────┐
                                    ▼               ▼                ▼
                          ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐
                          │ Fake        │  │ Fake        │  │ RealLinkedIn      │
                          │ X/IG/FB     │  │ LinkedIn    │  │ Adapter           │
                          │ Adapters    │  │ Adapter     │  │ (LINKEDIN_LIVE_   │
                          │ (sandbox)   │  │ (default)   │  │  MODE=true)       │
                          └─────────────┘  └─────────────┘  └──────────────────┘
```

## Data Model
- `Campaign` — source content + caption-generation parameters (dialect,
  tone, language, CTA, etc.)
- `SocialPost` — one row per platform per campaign, tracks status
  (queued → publishing → published/failed)
- `OAuthToken` — encrypted per-platform access/refresh tokens

Schema is managed exclusively via Alembic migrations, not `create_all`.

## Key Behavior
- Caption generation uses Groq (`openai/gpt-oss-120b`) at a fixed
  `temperature=0.7`.
- Campaign type changes generation behavior: Educational/Product campaigns
  trigger a full extraction and rewrite of source material; Opinion
  campaigns perform a near-verbatim light copyedit to preserve the
  author's original voice.
- LinkedIn publishes to the real API (behind an explicit
  `LINKEDIN_LIVE_MODE` flag); X, Instagram, and Facebook use fake/sandbox
  adapters for safe local testing.
