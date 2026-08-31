# KYC Onboarding System — Technical Decisions

## Why LangGraph over LangChain or plain Python logic
Identity verification isn't a linear path — it has loops (e.g. "image
unclear → ask user to resubmit → re-evaluate"). LangGraph's cyclical
execution and graph-based state management are what a robust, non-linear
decision flow like this actually needs. Bavly moved from thinking of
agents as single-shot responders to building complex, stateful execution
graphs specifically because of this project's requirements.

## Why multi-frame capture + LLM consolidation instead of single-image OCR
Relying on a single image extraction proved far too brittle — OCR
accuracy and consistency varied too much frame to frame. The pipeline was
redesigned to capture multiple frames of the document, extract from all
of them, and pass the full set of extractions to an LLM agent that
cross-references them, resolves inconsistencies, and makes the final call
— rather than trusting any single frame's read.

## Why a three-tier face-match threshold instead of binary match/no-match
A simple pass/fail on face similarity would over-reject genuine users
whose appearance has legitimately drifted from their ID photo (e.g. a new
beard, glasses). The three-tier threshold (pass / needs retake / manual
review) routes the ambiguous middle band to a human rather than an
automatic rejection, while still keeping clear high-confidence and
low-confidence auto-decisions.

## Why enhanced-only OCR (not raw)
Raw vs. CLAHE-enhanced OCR were tested head-to-head with a majority-vote
consensus experiment against ground truth; enhanced won, so the pipeline
runs enhanced OCR only. (Raw extraction is still available in
`OCREngine.extract_raw` for re-running that comparison later.)

## Why `needs_retake` is fail-fast with no local retry loop
Any step that can't get usable data (no card detected, blurry frame, no
face detected, unreadable expiry) routes straight to email_handoff on the
first failure — there's no bounded local retry loop built into the graph
itself. `manual_review` is reserved for exactly one case (an ambiguous
face-match score), since that's a genuine human judgment call rather than
a data-quality problem.
