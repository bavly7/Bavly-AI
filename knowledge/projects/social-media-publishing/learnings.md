# Social Campaign Publisher — Learnings

This project completely transformed Bavly's approach to backend
architecture. He shifted from writing "happy-path" code — assuming
everything works perfectly — to engineering for failure as the default
mindset.

He gained a deep, practical understanding of production-grade backend
concepts: implementing webhooks, designing for idempotency (ensuring a
post isn't published twice if a network request drops), using exponential
backoff for rate limits, and implementing secure authorization flows —
all learned by building the real thing under real API constraints, not
from a tutorial.
