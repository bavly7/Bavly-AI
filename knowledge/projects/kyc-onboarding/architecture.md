# KYC Onboarding System — Architecture

The system is a LangGraph-orchestrated pipeline (a graph of nodes with
conditional routing, not a linear script), built around a fail-fast
principle: any step that can't get usable data routes immediately to a
fallback rather than retrying locally.

## Pipeline Steps

1. **Liveness check** — first node in the graph. The user performs 3
   randomly-chosen movement challenges on camera (e.g. "turn your head
   right"). Fail here, and nothing else runs.
2. **ID capture** — 10 frames each of the front and back of the card. A
   YOLO model crops the card boundary, a second YOLO model locates each
   field (name, ID number, address, expiry date), and PaddleOCR reads
   each field per frame. A majority vote across the 10 frames produces
   the consensus value per field.
3. **Expiry validation** — an expired or unreadable date short-circuits
   the pipeline before the more expensive steps below run.
4. **Duplicate check** — rejects a second application using a national ID
   number that's already been approved.
5. **Face verification** — InsightFace embeddings compare the live
   selfie against the face photo cropped from the ID, using a three-tier
   threshold (not a binary match/no-match) to handle appearance drift
   (e.g. a beard or glasses not in the ID photo) without over-rejecting
   genuine users: high similarity → pass, low similarity → needs retake
   (a quality issue, not a block), ambiguous middle band → manual review.
6. **LLM consolidation** — a Groq-powered agent normalizes the OCR
   consensus per field, constrained so it can only select/lightly
   normalize among values that actually appeared in the OCR output —
   never invent one.
7. **Final decision** — approved, manual_review, rejected, or
   mobile_handoff_required.

Any image-quality problem anywhere in the pipeline (no card detected,
every frame too blurry, no face detected, unreadable expiry date, low
face similarity) routes to the same fallback: a magic-link email offering
to continue the session on a phone.

## Tech Stack

| Layer | Tech |
|---|---|
| Card / field detection | YOLO11 (Ultralytics), fine-tuned on a Roboflow Egyptian-ID dataset |
| OCR | PaddleOCR (Arabic), CLAHE + unsharp-mask enhancement |
| Face verification | InsightFace (ArcFace embeddings), cosine similarity |
| Liveness | MediaPipe Tasks API (FaceLandmarker, PoseLandmarker) |
| LLM consolidation | Groq |
| Orchestration | LangGraph |
| Backend | FastAPI, SQLAlchemy |
| Database | PostgreSQL (SQLite supported for local testing) |
| Frontend | Vanilla JS + HTML, browser camera capture |
