# Phase 3 — GitHub Webhook Setup Guide

This guide explains how to configure GitHub webhooks to automatically update your knowledge base when you push changes to the `knowledge/` folder.

## Overview

When you push changes to markdown files in `knowledge/`, the webhook:
1. Detects which files changed (added/modified/deleted)
2. Re-embeds changed content via Cohere
3. Updates the PostgreSQL database
4. Invalidates cached answers that referenced old content

## Setup Steps

### 1. Set Webhook Secret (Optional but Recommended)

Add to your `.env` file:

```bash
GITHUB_WEBHOOK_SECRET=your-random-secret-here
```

Generate a secure secret:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Configure GitHub Webhook

1. Go to your repo: `https://github.com/bavly7/Portfolio`
2. Navigate to **Settings → Webhooks → Add webhook**
3. Configure:
   - **Payload URL**: `https://your-backend.render.com/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: (paste the value from step 1)
   - **Which events**: Select "Just the push event"
   - **Active**: ✅ checked

### 3. Deploy Your Backend

Make sure your backend is deployed with the Phase 3 code:

```bash
# The webhook endpoint is now available at:
POST /webhook/github
```

### 4. Test the Webhook

After setup, make a test commit:

```bash
# Make a small change to any knowledge file
echo "\n## Test Update" >> knowledge/personal/bio.md

# Commit and push
git add knowledge/personal/bio.md
git commit -m "test: webhook integration"
git push origin main
```

Check your backend logs — you should see:
```
✅ Queued 1 file change(s) for processing
📄 Processing modified: personal/bio.md
  ~ updating chunk: personal/bio.md
```

## Manual Testing (Local Development)

Use the test payloads from `tests/test_webhook.py`:

```bash
# Test modifying a file
curl -X POST http://localhost:8000/webhook/github \
     -H 'Content-Type: application/json' \
     -d '{
       "ref": "refs/heads/main",
       "commits": [{
         "id": "test001",
         "message": "Update bio",
         "added": [],
         "modified": ["knowledge/personal/bio.md"],
         "removed": []
       }]
     }'
```

## How It Works

### File Change Detection

The webhook only processes:
- ✅ `.md` files in `knowledge/` folder
- ✅ On `main` or `master` branch pushes
- ❌ Ignores other files (README, code, etc.)

### Processing Logic

**Modified/Added files:**
1. Read file from disk (`knowledge/projects/...`)
2. Generate embedding via Cohere
3. Check if chunk exists in DB:
   - If content unchanged → skip (saves API calls)
   - If content changed → delete old chunk, insert new one
   - If new file → insert new chunk

**Deleted files:**
1. Delete all chunks where `file_path` matches
2. No embedding needed

### Cache Invalidation

When knowledge changes, all cached answers are cleared (conservative approach to avoid serving stale information).

Future optimization: track which answers referenced which chunks and only invalidate affected entries.

## File Path Mapping

GitHub sends: `knowledge/projects/kyc-onboarding/architecture.md`  
Database stores: `projects/kyc-onboarding/architecture.md`

(The `knowledge/` prefix is stripped during processing)

## Project Folder Mapping

The system maps project folders to database entries:

| Folder Name | Project Name (in DB) |
|------------|---------------------|
| `kyc-onboarding` | Automated KYC Onboarding System (Egyptian National ID) |
| `agentic-rag-retail` | Agentic RAG Retail Analytics |
| `social-media-publishing` | Social Campaign Publisher |
| `pulsefit` | PulseFit — AI-Powered Personal Trainer |

If you add a new project, update this mapping in `backend/ingestion.py`:

```python
PROJECT_FOLDER_MAP = {
    "kyc-onboarding": "Automated KYC Onboarding System (Egyptian National ID)",
    # ... add new projects here
}
```

## Troubleshooting

### Webhook not triggering

1. Check GitHub's webhook delivery page:
   - Settings → Webhooks → Recent Deliveries
2. Look for error responses (401, 500, etc.)
3. Verify your backend URL is publicly accessible

### Files not updating in database

1. Check backend logs for processing errors
2. Verify file exists in `knowledge/` folder
3. Ensure file is not a placeholder (`<!-- ... -->` only)
4. Check Cohere API key is valid and has quota

### Signature verification failing

If you get 401 errors:
1. Verify `GITHUB_WEBHOOK_SECRET` matches GitHub webhook secret
2. For local testing, you can temporarily remove the secret (webhook will accept unsigned requests)

## Rate Limits

**Cohere Free Tier:**
- ~30 requests/minute
- ~200K tokens/day

The webhook adds a 0.3-second delay between embeddings to stay under the rate limit. If you push many files at once, processing happens sequentially to avoid hitting the limit.

## Security Notes

1. **Always use a webhook secret in production** — without it, anyone can trigger your webhook endpoint
2. The signature verification uses HMAC SHA-256 and constant-time comparison to prevent timing attacks
3. Only pushes to `main`/`master` branch are processed
4. Only `.md` files in `knowledge/` are processed — other files are ignored

## Next Steps

After Phase 3 is working:
- **Phase 4**: Multilingual support (Egyptian Arabic)
- **Phase 5**: Voice I/O (STT/TTS)
- **Phase 6**: Character animation
- **Phase 7**: Polish (monitoring, rate limiting, optional MCP wrapper)
