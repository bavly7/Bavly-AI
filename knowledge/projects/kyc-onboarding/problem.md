# KYC Onboarding System — Problem

Standard identity-verification flows are often brittle and opaque: a
rejected submission gives the user little clear guidance, and re-submitting
the exact same document can inconsistently pass or fail depending on
image quality alone, not any change in the actual document.

This system solves that by separating genuine identity/fraud concerns
(routed to manual review) from simple image-quality problems (routed to
an immediate retry prompt via mobile handoff) — so most users get a fast,
automated, and consistent decision, and the few that need a human get
flagged for the right reason.
