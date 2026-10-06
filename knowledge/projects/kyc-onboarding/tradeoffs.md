# KYC Onboarding System — Trade-offs

- **No local retry loop for `needs_retake`.** Chosen to keep the graph
  simple and avoid trapping users in an infinite in-session loop, but it
  means there's currently no rate limit stopping someone from retrying
  indefinitely via repeated handoff requests — a deliberate scope
  decision, not an oversight, with rate-limiting noted as a next step.
- **No document-authenticity / anti-spoofing check on the ID card
  itself.** A printed photocopy or a photo-of-a-photo would currently
  pass. This is the document-side equivalent of face liveness and was
  scoped out from the start to keep the project focused, not forgotten.
- **`duplicate_check` only compares exact national ID numbers.** A
  face-embedding similarity search across applicants (catching someone
  re-applying under a different identity) would add real fraud-detection
  value, but needs its own vector index (e.g. pgvector) and threshold
  calibration — judged out of scope for the current version.
- **All numeric thresholds are unvalidated placeholders**, set from
  limited hand-testing rather than a calibrated validation set. Accepted
  as a starting point given project timeline, with a labeled validation
  pass identified as necessary future work.
- **SQLite used for local testing** even though the code is DB-agnostic
  via SQLAlchemy; the Postgres path hasn't been re-tested since the
  switch. A known gap, not a design choice to avoid Postgres.
