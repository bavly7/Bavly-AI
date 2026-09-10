"""
Phase 3 — GitHub Webhook Ingestion

Receives GitHub push webhooks, detects changes in knowledge/ folder,
and triggers re-embedding + cache invalidation for affected files.

SPECS.md §5 implementation: diff-based change detection, re-embed only
changed chunks, invalidate answer_cache entries tagged with affected projects.
"""

import hashlib
import hmac
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import HTTPException, Header, Request
from pydantic import BaseModel

load_dotenv()

GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
KNOWLEDGE_PREFIX = "knowledge/"


# ---------------------------------------------------------------------------
# Webhook payload models
# ---------------------------------------------------------------------------

class FileChange(BaseModel):
    """Represents a single file change from GitHub webhook"""
    path: str
    status: Literal["added", "modified", "removed"]


class WebhookPayload(BaseModel):
    """Simplified GitHub push webhook payload"""
    ref: str  # e.g., "refs/heads/main"
    commits: list[dict]


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------

def verify_signature(payload_body: bytes, signature_header: str | None) -> bool:
    """Verify GitHub webhook signature using HMAC SHA-256.

    Returns True if signature is valid or if GITHUB_WEBHOOK_SECRET is not set
    (allowing local testing without signature verification).
    """
    if not GITHUB_WEBHOOK_SECRET:
        # No secret configured — allow for local dev/testing
        return True

    if not signature_header:
        return False

    # GitHub sends signature as "sha256=<hex_digest>"
    if not signature_header.startswith("sha256="):
        return False

    expected_signature = signature_header.split("=")[1]

    # Compute HMAC
    mac = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    computed_signature = mac.hexdigest()

    return hmac.compare_digest(computed_signature, expected_signature)


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------

def extract_file_changes(payload: dict) -> list[FileChange]:
    """Extract all file changes from webhook payload commits.

    Returns only changes within knowledge/ folder, with paths relative to
    repo root (e.g., "knowledge/projects/kyc-onboarding/architecture.md").
    """
    changes: dict[str, FileChange] = {}  # deduplicate by path

    for commit in payload.get("commits", []):
        # GitHub includes added, removed, modified arrays per commit
        for added_file in commit.get("added", []):
            if added_file.startswith(KNOWLEDGE_PREFIX) and added_file.endswith(".md"):
                changes[added_file] = FileChange(path=added_file, status="added")

        for modified_file in commit.get("modified", []):
            if modified_file.startswith(KNOWLEDGE_PREFIX) and modified_file.endswith(".md"):
                changes[modified_file] = FileChange(path=modified_file, status="modified")

        for removed_file in commit.get("removed", []):
            if removed_file.startswith(KNOWLEDGE_PREFIX) and removed_file.endswith(".md"):
                changes[removed_file] = FileChange(path=removed_file, status="removed")

    return list(changes.values())


def normalize_file_path(github_path: str) -> str:
    """Convert GitHub webhook path to our internal file_path format.

    GitHub sends: "knowledge/projects/kyc-onboarding/architecture.md"
    We store:     "projects/kyc-onboarding/architecture.md"

    (strips the "knowledge/" prefix to match populate_db.py's format)
    """
    if github_path.startswith(KNOWLEDGE_PREFIX):
        return github_path[len(KNOWLEDGE_PREFIX):]
    return github_path


# ---------------------------------------------------------------------------
# Route handlers (imported by main.py)
# ---------------------------------------------------------------------------

async def handle_github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None)
) -> dict:
    """
    FastAPI route handler for POST /webhook/github

    Verifies signature, extracts changed files, and returns them for processing.
    Actual re-embedding logic lives in ingestion.py (separation of concerns).
    """
    # Read raw body for signature verification
    payload_body = await request.body()

    # Verify signature
    if not verify_signature(payload_body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")

    # Only process pushes to main branch
    ref = payload.get("ref", "")
    if ref not in ("refs/heads/main", "refs/heads/master"):
        return {
            "status": "ignored",
            "reason": f"Not a push to main/master (ref={ref})"
        }

    # Extract changed files
    file_changes = extract_file_changes(payload)

    if not file_changes:
        return {
            "status": "ignored",
            "reason": "No .md files changed in knowledge/ folder"
        }

    # Return changes for processing by ingestion.py
    # (actual processing happens after response is sent, to avoid webhook timeout)
    return {
        "status": "queued",
        "changes": [
            {
                "path": normalize_file_path(fc.path),
                "status": fc.status
            }
            for fc in file_changes
        ]
    }
