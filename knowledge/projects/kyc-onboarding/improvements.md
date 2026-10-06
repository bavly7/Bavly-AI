# KYC Onboarding System — What Would Be Improved

- Fix the liveness frame-ordering bug (persist explicit
  frame-to-instruction pairing) and re-test.
- Point `FRONTEND_BASE_URL` at a real LAN-reachable address and re-test
  the mobile handoff flow end to end.
- Switch `DATABASE_URL` to Postgres and re-test (code is already
  DB-agnostic via SQLAlchemy).
- Build a small labeled validation set and run a real accuracy
  evaluation: OCR field accuracy, face-match precision/recall,
  false-accept/false-reject rate — replacing today's placeholder
  thresholds with calibrated ones.
- Containerize with Docker Compose (backend + Postgres + model
  inference) — not yet started.
- Rate-limit `needs_retake`/handoff attempts at the API layer.
- Replace the fixed CLAHE + unsharp-mask enhancement with a
  vision-agent-based step that inspects each frame and applies whatever
  correction it specifically needs (deglare, deblur, exposure correction)
  rather than one static filter applied uniformly — worth prototyping
  against the same raw-vs-enhanced consensus methodology already used
  elsewhere in the project, rather than assuming it's strictly better
  without measurement.
- Cross-check extracted names against an identity-data provider (e.g.
  LexisNexis) as an additional duplicate/fraud signal beyond exact
  ID-number matching — would need real scoping around false-positive risk
  before it could avoid flooding manual review.
