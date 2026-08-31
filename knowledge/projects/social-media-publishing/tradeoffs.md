# Social Campaign Publisher — Trade-offs

- **Real LinkedIn integration, sandboxed everything else.** Chose depth
  on one platform (proving out a genuinely working live integration) over
  breadth across all four — a deliberate scoping decision given the
  20-week internship timeline, not a sign the other adapters are
  unfinished by accident.
- **No hard character-limit truncation for X captions.** An early
  safety-net that hard-truncated X captions at the platform's character
  limit was dropped in favor of more advanced prompt-based length
  guidance. This means captions may occasionally exceed X's limit and
  need manual trimming before publishing — a trade favoring generation
  quality/flexibility over a guaranteed hard constraint.
- **APScheduler instead of a distributed job queue.** Simpler to
  implement and sufficient for a single-node deployment, but carries a
  real risk of duplicate publishing jobs if the system were ever
  horizontally scaled across multiple worker nodes without adding a
  centralized distributed lock.
- **No centralized environment-loading module originally** — several
  files independently call `load_dotenv()` rather than going through one
  shared config entrypoint, a known rough edge rather than an intentional
  design choice.
- **Single active OAuth token per platform.** The schema assumes one
  connected account per platform; multiple accounts per platform aren't
  supported, a scope-limiting decision appropriate for a capstone/demo
  system.
