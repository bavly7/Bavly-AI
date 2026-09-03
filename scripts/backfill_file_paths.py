"""
Backfill file_path and chunk_index for existing knowledge_chunks.

Run this AFTER running the SQL migration (add_file_path_columns.sql)
but BEFORE re-running populate_db.py.

This script:
  1. Reads all .md files under knowledge/
  2. Matches each existing chunk's content to its source file
  3. Updates file_path and chunk_index columns

Run from the project root:
    python scripts/backfill_file_paths.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent / "knowledge"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def build_content_to_path_map():
    """
    Scan all .md files under knowledge/ and build a mapping:
    {content_hash: file_path}

    We use content matching since that's the most reliable way to
    identify which file a chunk came from.
    """
    content_to_path = {}

    # personal/
    personal_dir = KNOWLEDGE_ROOT / "personal"
    for md_file in sorted(personal_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8").strip()
        if content:
            content_to_path[content] = str(md_file.relative_to(KNOWLEDGE_ROOT)).replace("\\", "/")

    # experience/<company>/*.md
    experience_dir = KNOWLEDGE_ROOT / "experience"
    for company_dir in sorted(experience_dir.iterdir()):
        if not company_dir.is_dir():
            continue
        for md_file in sorted(company_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8").strip()
            if content:
                content_to_path[content] = str(md_file.relative_to(KNOWLEDGE_ROOT)).replace("\\", "/")

    # projects/<project>/*.md
    projects_dir = KNOWLEDGE_ROOT / "projects"
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        for md_file in sorted(project_dir.glob("*.md")):
            content = md_file.read_text(encoding="utf-8").strip()
            if content:
                content_to_path[content] = str(md_file.relative_to(KNOWLEDGE_ROOT)).replace("\\", "/")

    return content_to_path


def backfill():
    content_to_path = build_content_to_path_map()
    print(f"Found {len(content_to_path)} files in knowledge/ directory")

    session = Session()
    try:
        # Fetch all existing chunks
        result = session.execute(text("SELECT id, content FROM knowledge_chunks"))
        chunks = result.fetchall()
        print(f"Found {len(chunks)} existing chunks in database")

        matched = 0
        unmatched = 0

        for chunk_id, content in chunks:
            if content in content_to_path:
                file_path = content_to_path[content]
                session.execute(
                    text("UPDATE knowledge_chunks SET file_path = :fp, chunk_index = 0 WHERE id = :id"),
                    {"fp": file_path, "id": chunk_id}
                )
                print(f"  ✓ Updated: {file_path}")
                matched += 1
            else:
                # This chunk doesn't match any current file - might be old/deleted
                # Leave it with NULL file_path (manual chunk)
                print(f"  ✗ No match for chunk {chunk_id} (content preview: {content[:50]}...)")
                unmatched += 1

        session.commit()
        print(f"\nDone! Matched: {matched}, Unmatched: {unmatched}")
        print("\nUnmatched chunks are left with NULL file_path (treated as manual chunks).")

    finally:
        session.close()


if __name__ == "__main__":
    backfill()