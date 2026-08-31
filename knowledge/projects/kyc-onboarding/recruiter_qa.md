# KYC Onboarding System — Recruiter Q&A

Q: Why did you choose LangGraph over LangChain or plain Python logic?
A: Identity verification isn't a linear path — it has loops, like "image
unclear → ask user to resubmit → re-evaluate." LangGraph's cyclical
execution and graph-based state management are exactly what's needed to
build that kind of robust, non-linear logic, rather than forcing a loopy
process into a straight-line script.

Q: How does the system avoid the LLM inventing or guessing identity data?
A: The LLM consolidation agent is constrained so it can only select or
lightly normalize among values that actually appeared in the OCR output
across multiple frames — it's never allowed to invent a value that wasn't
extracted from the actual document.

Q: Why not just reject on any face-match uncertainty to be safe?
A: A binary match/no-match would over-reject genuine users whose
appearance has legitimately drifted from their ID photo (a new beard,
glasses, etc.). The three-tier threshold routes only the genuinely
ambiguous cases to a human, keeping high-confidence and low-confidence
cases fully automated.

Q: Has this been measured for real-world accuracy?
A: Not yet — this is an honest, disclosed gap. The pipeline runs
end-to-end successfully in demos, but no field-level OCR accuracy or
face-match precision/recall has been measured against a labeled
validation set yet, so current thresholds are placeholders rather than
calibrated values. That's explicitly the next step.
