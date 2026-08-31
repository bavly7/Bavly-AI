# KYC Onboarding System — Challenges

## The hardest problem: OCR accuracy and inconsistency

The biggest challenge was dealing with OCR accuracy and inconsistency —
relying on a single image extraction was far too brittle. A single frame
could easily misread a field due to glare, motion blur, or angle, and
there was no way to know that had happened from the frame alone.

The fix was to redesign the capture pipeline to grab multiple frames of
the document instead of one, and rather than picking a single "best"
frame, pass all the extracted data to an LLM agent acting as a smart
decision-maker — cross-referencing the extractions, resolving
inconsistencies between them, and making the final, accurate call on what
the data actually says. This shifted the reliability of the system from
depending on one lucky (or unlucky) frame to depending on consensus
across many.

## Other known rough edges (documented, not hidden)

- A liveness frame-ordering bug: frames can be re-read in a different
  order than they were captured (via directory glob, which doesn't
  guarantee order), which can cause inconsistent pass/fail behavior
  between the immediate liveness check and the final graph result. Fix
  identified (persist explicit frame-to-instruction pairing) but not yet
  applied.
- No end-to-end accuracy evaluation has been run yet — all numeric
  thresholds (blur, face-match, liveness) are placeholders from limited
  hand-testing, not a calibrated validation set.
