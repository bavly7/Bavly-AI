# Social Campaign Publisher — Challenges

## The hardest problem: real LinkedIn OAuth integration

The hardest challenge was implementing real LinkedIn authorization and
standardizing it across the system through the Adapter Pattern. Building
the LinkedIn adapter was Bavly's first deep dive into real-world OAuth
flows, token exchanges, and managing real API permissions — not a
simulated or sandboxed version of these concepts, but the real thing with
real constraints.

Figuring out the exact handshake for LinkedIn's API, securely managing
access tokens, and mapping LinkedIn's specific response structures into
the system's unified adapter interface took a lot of trial and error and
deep reading of LinkedIn's documentation. A genuinely tough engineering
hurdle, but one that directly produced the deepest learning of the
project (see `learnings.md`).

## Other known rough edges (documented, not hidden)

- The "reaper job" gap: sandbox adapters simulate async delivery via
  webhooks; if a webhook fails to arrive, a post can remain stuck in
  "publishing" state forever, with no background job yet implemented to
  clean up or fail orphaned posts.
- Alembic's autogenerate doesn't reliably detect new Python Enum values —
  adding a new platform in the future requires a manual migration
  statement rather than fully automatic detection.
- No automated post-generation validation exists to catch and retry a
  caption that drifts from the required language/dialect instruction,
  since generation is inherently non-deterministic at `temperature=0.7`.
