# PulseFit — Architecture

## End-to-End Flow
1. Sign up / log in — session-based auth backed by SQLite.
2. Fill a fitness questionnaire (experience level, goal, training days,
   injuries, weak muscles, available equipment, gender, activity level).
3. Get an auto-generated workout split — a rule-based recommendation
   engine picks the training split, exercises, sets, and reps, balancing
   volume, fatigue, and equipment diversity for that user.
4. Train with the AI camera coach — pose estimation detects the body,
   counts reps by tracking joint angles through each rep's stages,
   detects form errors per exercise, and gives live corrective voice
   feedback in Arabic or English (cached TTS so repeated cues don't
   regenerate audio).
5. Log meals — search foods in English, Arabic, or Franco-Arabic (e.g.
   "fera5", "roz", "3enab"); the app normalizes the query, matches
   against a local Egyptian food database, applies cooking-method
   multipliers, and falls back to an LLM (Groq) lookup for anything not
   in the database.
6. Track macros — BMR/TDEE and calorie/macro targets derived from the
   user's profile and goal (bulk/cut/maintain/strength).
7. Review progress — dashboard, workout history, weekly stats.
8. Installable as a Progressive Web App (manifest + service worker).

## AI/CV Core
- **Pose estimation:** real-time human pose keypoints per video frame,
  used to compute joint angles for rep counting and form checking.
- **Per-exercise trainers:** ~90 individual Python classes (one per
  exercise), each implementing its own state machine (up/down stage
  tracking), rep counter, and exercise-specific form rules.
- **Hybrid inference:** most exercises run pose inference server-side
  (YOLO11-pose); at least one runs client-side in the browser via
  MediaPipe Pose, streamed directly from the webcam with no server
  round-trip — both architectures coexist in the same product.
- **Voice AI Coach:** a shared `AICoach` engine turns form errors into
  contextual spoken cues, using gTTS, a local MP3 cache to avoid
  regenerating repeated phrases, and a background queue/thread so audio
  doesn't block the video loop.
- **Workout recommender:** a constraint-based, deterministic and
  explainable engine that scores exercises using tags (e.g.
  `stretch_focused`, `unilateral`, `high_stability`), enforces per-muscle
  volume targets by experience level, applies a fatigue-cost budget per
  session, blocks unsafe exercise pairings, and reasons about
  injuries/equipment/weak-point priorities.
- **Nutrition NLP:** a Franco-Arabic → English normalization layer plus
  fuzzy matching (`difflib`) against a curated food database, with a Groq
  LLM call as a fallback for foods outside the local dataset.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Python, Flask, Gunicorn |
| CV / pose estimation | YOLO11-pose (server-side), MediaPipe Pose (client-side) |
| Numerical / CV utilities | OpenCV (headless), NumPy |
| LLM integration | Groq API |
| Text-to-speech | gTTS, pygame, local MP3 caching |
| Database | SQLite |
| Auth | Session-based, hashed passwords |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| PWA | Web App Manifest, Service Worker |
| Containerization | Docker, deployed on Railway |
