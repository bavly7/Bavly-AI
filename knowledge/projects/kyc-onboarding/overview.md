# KYC Onboarding System — Overview

Automated KYC Onboarding System (Egyptian National ID) is an end-to-end
identity-verification pipeline. A user submits a photo of their Egyptian
national ID (front and back) and a liveness-checked selfie through the
browser. A LangGraph-orchestrated agent extracts identity data, verifies
the user is a live person who matches the ID photo, and returns one of
four automated decisions: approve, manual review, reject, or mobile
handoff — with no manual review needed for the large majority of cases.

**GitHub:** `Automated-KYC-Onboarding-System-Egyptian-National-ID`
**Tech stack:** LangGraph, YOLO11, PaddleOCR, InsightFace, MediaPipe,
FastAPI, PostgreSQL
