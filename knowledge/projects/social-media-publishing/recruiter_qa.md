# Social Campaign Publisher — Recruiter Q&A

Q: Why did you implement a custom Adapter Pattern for the platforms
instead of just writing direct API calls?
A: Scalability and maintainability. Every platform handles media uploads
and text limits differently (e.g. LinkedIn's multi-step image upload vs.
standard endpoints). By using the Adapter Pattern, the core campaign
engine doesn't need to know how LinkedIn works; it just calls a
standardized `publish()` method. To add Twitter or Facebook as real
integrations later, it's a new adapter, not a change to the core logic.

Q: How did you handle the risk of duplicate posts if an API call fails or
times out?
A: By implementing idempotency keys and retry mechanisms with exponential
backoff. If the system doesn't get a clear success response, it can
safely retry the request without risking spamming the user's LinkedIn
feed with duplicate posts.

Q: Why did you include a manual review step instead of fully automating
the AI publishing?
A: In production, AI is unpredictable. Brands cannot afford an LLM
hallucinating a controversial opinion or a broken link on their official
channels. The manual review step (human-in-the-loop) combines the speed
of AI generation with the safety of human oversight — a mandatory
architecture choice for enterprise generative AI, not an optional
add-on.

Q: This started as a much simpler internship requirement — why go beyond
scope?
A: The original ask was a basic scheduled publisher with a manually
written caption. Bavly saw an opportunity to build something that
actually demonstrated production-level system design — campaign intents,
platform-aware generation, real OAuth, idempotent publishing — rather
than just meeting the minimum bar, and the FlyRank team's feedback
specifically recognized that initiative.
