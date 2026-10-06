# PulseFit — Recruiter Q&A

Q: Why use a deterministic/rule-based recommender initially instead of
Machine Learning from day one?
A: The cold-start problem and user safety. A new user has zero historical
fitness data — training an ML model on generic data might recommend a
workout that causes injury. Starting with a rule-based engine grounded in
trusted ACSM sports science guarantees a safe, reliable workout from day
one. As the user logs workouts, the system builds a personalized dataset
to enable a safe transition into ML-based recommendations later.

Q: Why a hybrid server/client inference approach for the computer vision?
Why not run it all on the backend?
A: A deliberate trade-off balancing latency, privacy, and compute cost.
Streaming live video frames to a backend server for pose estimation
creates significant network latency and would be expensive in cloud GPU
cost at scale. Users also don't want live exercise video sent to a
server — a real privacy concern. Running lightweight pose extraction on
the client edge and sending only structured keypoint coordinates (a few
bytes of JSON) to the backend for the heavier logic lets the app run in
real time, scale cheaply, and protect user privacy.

Q: How do you know the workout recommendations are actually safe, not
just "explainable"?
A: The engine is grounded in ACSM (American College of Sports Medicine)
guidelines rather than an arbitrary rule set — every recommendation
traces back to a specific volume, fatigue, or scoring rule derived from
established sports science, which also makes it explainable in a
graduation defense or technical interview context.

Q: What was the biggest constraint building this?
A: Team size relative to scope — a 2-person team built computer vision,
NLP, a recommendation engine, and full-stack development simultaneously,
which forced ruthless prioritization of what actually shipped in V1
versus what was deferred to the V2 vision.
