# Social Campaign Publisher — What Would Be Improved

- Implement a background "reaper" job to detect and fail orphaned posts
  stuck in the "publishing" state when a sandbox webhook never arrives.
- Add automated post-generation validation to catch and retry captions
  that drift from the required language/dialect instruction, rather than
  relying solely on prompt instruction at a non-zero temperature.
- Re-introduce a hard character-limit safety net for X captions alongside
  the prompt-based length guidance, to guarantee platform compliance
  rather than relying on generation quality alone.
- Centralize environment-variable loading into one shared config
  entrypoint instead of multiple independent `load_dotenv()` calls.
- Add a centralized distributed lock if the system is ever deployed
  across multiple worker nodes, to eliminate the duplicate-job risk in
  APScheduler under horizontal scaling.
- Extend real (non-sandboxed) integrations to X, Instagram, and Facebook,
  following the same OAuth pattern proven out with LinkedIn.
- Support multiple connected accounts per platform, not just one.
