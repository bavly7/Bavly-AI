# PulseFit — Technical Decisions

## Why a deterministic/rule-based recommender instead of ML from day one
The cold-start problem and user safety. A new user has zero historical
fitness data. Training an ML model on generic data might recommend a
workout that causes injury. Starting with a rule-based engine grounded in
trusted ACSM sports science guarantees a safe, reliable workout from day
one. As the user logs workouts, the system builds a personalized dataset
that can later support a safer transition into ML-based recommendations
(see V2 plans in `improvements.md`).

## Why a hybrid server/client inference approach for computer vision
A deliberate trade-off balancing latency, privacy, and compute cost.
Streaming live video frames to a backend server for pose estimation
creates significant network latency and would be expensive at scale in
cloud GPU cost. Users also don't want live video of themselves exercising
sent to a server — a real privacy concern. Running lightweight pose
extraction on the client edge (browser) and sending only structured
keypoint coordinates (a few bytes of JSON) to the backend for the heavier
counting/form-correction logic lets the app run in real time, scale
cheaply, and protect user privacy — while still demonstrating both
architectures within the same product.

## Why ~90 separate per-exercise trainer classes instead of one generic
## exercise-tracking system
Each exercise has genuinely different joint-angle geometry, rep-stage
definitions, and failure modes (e.g. squat depth vs. elbow flare on a
curl) — a single generic tracker couldn't capture exercise-specific form
rules accurately. Modeling each exercise as its own class with its own
state machine keeps the per-exercise logic explicit and independently
testable, at the cost of more total code to maintain.

## Why gTTS with local caching instead of calling TTS live every time
Repeated coaching cues (e.g. "keep your back straight") happen constantly
during a single workout. Caching generated audio locally avoids
regenerating the same phrase's audio repeatedly, keeping the coaching
feedback loop fast and reducing unnecessary API calls.
