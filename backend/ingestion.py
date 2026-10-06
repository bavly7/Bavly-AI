"""
Phase 3 — GitHub Ingestion Pipeline

Handles re-embedding and cache invalidation when knowledge/ files change.

Core logic:
  - Modified: re-chunk, re-embed, replace old chunks (delete + insert)
  - Added: chunk, embed, insert new chunks
  - Removed: delete all chunks with matching file_path

Per RULES.md #11: manually-provided project narrative (why/how/challenges)
is owner-supplied, not auto-generated from GitHub — this pipeline only
handles re-embedding existing .md files when they change, never fabricates
narrative content.
"""

import os
import time
import uuid
from pathlib import Path
from typing import Literal

import cohere
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.models import KnowledgeChunk, Project

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
COHERE_API_KEY = os.environ["COHERE_API_KEY"]

# Path to knowledge/ folder in the repo
# Assuming webhook receiver is running from repo root
KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent / "knowledge"

co = cohere.Client(COHERE_API_KEY)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------

def embed(text: str) -> list[float]:
    """Generate a single embedding via Cohere multilingual v3.0.
    input_type='search_document' is used for stored content."""
    try:
        print(f"  ⏳ Generating embedding ({len(text)} chars)...")
        resp = co.embed(
            texts=[text],
            model="embed-multilingual-v3.0",
            input_type="search_document",
        )
        print(f"  ✅ Embedding generated")
        return resp.embeddings[0]
    except Exception as e:
        print(f"  ❌ Embedding failed: {e}")
        raise


def detect_language(text: str) -> str:
    """Rough heuristic: if text contains Arabic characters, tag ar-EG, else en."""
    arabic_chars = sum(1 for c in text if "؀" <= c <= "ۿ")
    return "ar-EG" if arabic_chars > 20 else "en"


# ---------------------------------------------------------------------------
# Helper: Folder name to nice title
# ---------------------------------------------------------------------------

def folder_name_to_title(folder_name: str) -> str:
    """
    Convert a kebab-case folder name to a nice capitalized title.

    Examples:
        "kyc-onboarding" -> "KYC Onboarding"
        "agentic-rag-retail" -> "Agentic RAG Retail"
        "my-new-project" -> "My New Project"
    """
    # Split on hyphens, capitalize each word
    words = folder_name.split("-")

    # Special case: known acronyms that should stay uppercase
    acronyms = {"kyc", "rag", "ai", "ml", "cv", "nlp", "api", "ui", "ux"}

    title_words = []
    for word in words:
        if word.lower() in acronyms:
            title_words.append(word.upper())
        else:
            title_words.append(word.capitalize())

    return " ".join(title_words)


# ---------------------------------------------------------------------------
# Project ID resolution
# ---------------------------------------------------------------------------

def resolve_project_id(file_path: str, session) -> tuple[str, str | None, str | None, str | None]:
    """
    Given a normalized file_path like "projects/kyc-onboarding/architecture.md",
    determine:
      1. source_type (personal_bio | experience | project_narrative | github_readme)
      2. project_id (UUID if applicable, else None)
      3. project_name (extracted from path for metadata filtering, e.g., "kyc")
      4. company_name (extracted from path for experience, e.g., "elevvo")

    Returns: (source_type, project_id, project_name, company_name)

    Phase 5.1 Metadata Extraction Rules:
    - projects/kyc-onboarding/* → project_name="kyc", company_name=None
    - experience/elevvo/* → project_name=None, company_name="elevvo"
    - personal/* → project_name=None, company_name=None
    """
    parts = file_path.split("/")

    if parts[0] == "personal":
        return "personal_bio", None, None, None

    if parts[0] == "experience" and len(parts) >= 2:
        company_folder = parts[1]  # e.g., "elevvo", "flyrank", "nti"
        # Extract company name (lowercase, normalized)
        company_name = company_folder.lower().strip()
        return "experience", None, None, company_name

    if parts[0] == "projects" and len(parts) >= 3:
        folder_name = parts[1]  # e.g., "kyc-onboarding"
        file_name = parts[-1]   # e.g., "architecture.md"

        # Direct database lookup by folder_name (no hardcoded map needed!)
        row = session.execute(
            text("SELECT id FROM projects WHERE folder_name = :folder"),
            {"folder": folder_name}
        ).fetchone()

        if not row:
            # Auto-create missing project
            print(f"📦 New project folder detected: '{folder_name}' — auto-creating database entry")

            # Generate a nice title from folder name
            project_name = folder_name_to_title(folder_name)

            # Create new project record
            new_project = Project(
                id=uuid.uuid4(),
                name=project_name,
                folder_name=folder_name,
                github_repo=None,  # Can be filled manually later
                tech_stack=[],
                summary=f"Auto-generated project entry for {project_name}",
            )
            session.add(new_project)
            session.flush()  # Get the ID immediately

            project_id = str(new_project.id)
            print(f"   ✅ Created project: {project_name} (ID: {project_id})")
            print(f"   💡 Update later with: UPDATE projects SET github_repo=..., tech_stack=..., summary=... WHERE id='{project_id}'")
        else:
            project_id = str(row.id)

        # Determine source_type
        source_type = "github_readme" if file_name == "github_metadata.md" else "project_narrative"

        # Extract project_name for metadata filtering (full folder name)
        # FIXED: Use full folder name instead of truncating at first hyphen
        # e.g., "kyc-onboarding" → "kyc-onboarding", "skin-cancer-gan-augmentation" → "skin-cancer-gan-augmentation"
        project_name_meta = folder_name.lower()

        return source_type, project_id, project_name_meta, None

    # Fallback
    return "project_narrative", None, None, None


# ---------------------------------------------------------------------------
# Change processing
# ---------------------------------------------------------------------------

def process_file_change(
    file_path: str,
    status: Literal["added", "modified", "removed"],
    session
) -> None:
    """
    Process a single file change:
      - added/modified: re-chunk, re-embed, upsert into knowledge_chunks
      - removed: delete all chunks with matching file_path
    """
    if status == "removed":
        _delete_chunks(file_path, session)
        return

    # For added/modified: read file, chunk, embed, upsert
    full_path = KNOWLEDGE_ROOT / file_path
    if not full_path.exists():
        print(f"⚠️ File not found on disk: {full_path} (skipping)")
        return

    content = full_path.read_text(encoding="utf-8").strip()
    if not content:
        print(f"⚠️ File is empty: {file_path} (skipping)")
        return

    # Skip placeholder-only files
    if content.startswith("<!--") and content.endswith("-->") and len(content) < 500:
        print(f"  - skipping placeholder-only file: {file_path}")
        return

    # Resolve source_type, project_id, and metadata (Phase 5.1)
    source_type, project_id, project_name, company_name = resolve_project_id(file_path, session)

    # NEW: Check for tech_stack.md file and populate projects.tech_stack
    if source_type in ("project_narrative", "github_readme") and project_id:
        tech_stack_file_path = file_path.rsplit("/", 1)[0] + "/tech_stack.md"
        tech_stack_path = KNOWLEDGE_ROOT / tech_stack_file_path

        if tech_stack_path.exists():
            tech_stack_content = tech_stack_path.read_text(encoding="utf-8").strip()
            # Remove markdown header if present (e.g., "# Project Name — Tech Stack")
            lines = [line.strip() for line in tech_stack_content.split("\n") if line.strip()]
            tech_line = lines[-1] if lines else ""  # Get last non-empty line (the actual tech list)

            if tech_line and not tech_line.startswith("#"):
                tech_stack = [t.strip() for t in tech_line.split(",") if t.strip()]

                # Update project's tech_stack
                session.execute(
                    text("UPDATE projects SET tech_stack = :tech WHERE id = :id"),
                    {"tech": tech_stack, "id": project_id}
                )
                print(f"  ✅ Updated tech_stack for project {project_id}: {len(tech_stack)} technologies")

    # Check if chunk already exists
    existing = session.query(KnowledgeChunk).filter_by(file_path=file_path, chunk_index=0).first()

    if existing:
        # Content unchanged? Skip re-embedding
        if existing.content == content:
            print(f"  = chunk unchanged: {file_path}")
            return

        # Content changed: delete old, will re-insert below
        session.delete(existing)
        session.flush()  # Commit the deletion before inserting new chunk
        print(f"  ~ updating chunk: {file_path}")
    else:
        print(f"  + adding chunk: {file_path}")

    # Generate embedding
    language = detect_language(content)
    vector = embed(content)

    # Insert new chunk with metadata (Phase 5.1)
    chunk = KnowledgeChunk(
        source_type=source_type,
        project_id=project_id,
        content=content,
        embedding=vector,
        language=language,
        file_path=file_path,
        chunk_index=0,  # one chunk per file for now
        project_name=project_name,  # Phase 5.1: metadata for pre-filtering
        company_name=company_name,  # Phase 5.1: metadata for pre-filtering
    )
    session.add(chunk)
    session.flush()  # get the new chunk ID

    # Rate limiting for Cohere free tier
    time.sleep(0.3)


def _delete_chunks(file_path: str, session) -> None:
    """Delete all chunks with matching file_path."""
    deleted = session.query(KnowledgeChunk).filter_by(file_path=file_path).delete()
    if deleted > 0:
        print(f"  - deleted {deleted} chunk(s) for {file_path}")


# ---------------------------------------------------------------------------
# Cache invalidation
# ---------------------------------------------------------------------------

def invalidate_cache_for_changes(file_paths: list[str], session) -> None:
    """
    Invalidate answer_cache entries that referenced chunks from changed files.

    Strategy: For each changed file_path, find all project_ids that were
    affected, then delete cache entries tagged with those project_ids.

    NOTE: Current schema has project_id_tags in answer_cache but we're not
    populating it yet in graph.py — this is placeholder logic for when we do.
    For now, we'll just clear all cache (conservative approach).
    """
    # Conservative approach: clear entire cache when knowledge changes
    # (Avoids serving stale answers that referenced now-outdated chunks)
    deleted = session.execute(text("DELETE FROM answer_cache")).rowcount
    if deleted > 0:
        print(f"  ⚠️ Cleared {deleted} cached answer(s) due to knowledge update")


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------

def process_webhook_changes(changes: list[dict]) -> dict:
    """
    Main entry point for processing GitHub webhook changes.

    changes: list of {"path": str, "status": "added"|"modified"|"removed"}

    Returns: summary dict with processing results
    """
    session = Session()
    results = {
        "processed": 0,
        "failed": 0,
        "cache_invalidated": False,
    }

    try:
        file_paths = []
        for change in changes:
            try:
                file_path = change["path"]
                status = change["status"]
                file_paths.append(file_path)

                print(f"\n📄 Processing {status}: {file_path}")
                process_file_change(file_path, status, session)
                results["processed"] += 1

            except Exception as e:
                print(f"❌ Failed to process {change['path']}: {e}")
                results["failed"] += 1
                # Don't raise — continue processing other files

        # Commit all changes
        session.commit()

        # Invalidate cache
        invalidate_cache_for_changes(file_paths, session)
        results["cache_invalidated"] = True

        # Commit cache invalidation
        session.commit()

    except Exception as e:
        session.rollback()
        print(f"❌ Fatal error during processing: {e}")
        raise

    finally:
        session.close()

    return results
