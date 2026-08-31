# PulseFit — Trade-offs

- **Rule-based recommender instead of ML from day one.** Traded a
  potentially more adaptive system for guaranteed safety on a cold start
  — no historical data means an ML model could easily recommend
  something unsafe for a specific new user's actual capacity.
- **Hybrid server/client CV inference instead of one consistent
  approach.** Chose complexity (maintaining two inference paths) in
  exchange for real latency, cost, and privacy benefits — a deliberate
  trade rather than an inconsistency.
- **~90 separate exercise classes instead of a generalized tracker.**
  Traded more total code and maintenance surface for per-exercise
  accuracy and explainability — each exercise's rules are independently
  understandable and testable rather than folded into one complex
  general-purpose system.
- **SQLite instead of a production database.** Reasonable for a
  graduation project's scope and timeline, deployed on Railway; not
  designed for multi-instance production scale as-is.
- **2-person team building a large-scope system.** Necessitated ruthless
  feature prioritization; some depth (e.g. a fully ML-personalized
  recommender, broader client-side pose coverage) was consciously
  deferred to V2 rather than attempted within the original scope.
