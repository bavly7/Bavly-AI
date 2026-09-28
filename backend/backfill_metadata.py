"""
Phase 5.1 — Backfill Metadata Script

Populates project_name and company_name columns for existing knowledge_chunks
by parsing their file_path values.

Run after migration: python -m backend.backfill_metadata

This script extracts metadata from file paths following the same logic as the
updated ingestion pipeline:
- projects/kyc-onboarding/* → project_name="kyc", company_name=None
- experience/elevvo/* → project_name=None, company_name="elevvo"
- personal/* → project_name=None, company_name=None
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path so we can import backend modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def extract_metadata_from_path(file_path: str) -> tuple[str | None, str | None]:
    """
    Extract project_name and company_name from a file_path.

    Returns: (project_name, company_name)

    Examples:
        "projects/kyc-onboarding/architecture.md" → ("kyc", None)
        "experience/elevvo/overview.md" → (None, "elevvo")
        "personal/bio.md" → (None, None)
    """
    if not file_path:
        return None, None

    parts = file_path.split("/")

    # Personal bio: no metadata
    if parts[0] == "personal":
        return None, None

    # Experience: extract company_name from second part
    if parts[0] == "experience" and len(parts) >= 2:
        company_name = parts[1].lower().strip()
        return None, company_name

    # Projects: extract project_name (first word before hyphen)
    if parts[0] == "projects" and len(parts) >= 2:
        folder_name = parts[1]
        # Take first part before hyphen as project_name
        # e.g., "kyc-onboarding" → "kyc", "pulsefit" → "pulsefit"
        project_name = folder_name.split("-")[0].lower()
        return project_name, None

    # Fallback: no metadata
    return None, None


def backfill_metadata():
    """Main backfill function."""
    session = Session()

    try:
        # Fetch all chunks with file_paths that need backfilling
        print("🔍 Fetching chunks to backfill...")
        rows = session.execute(
            text("""
                SELECT id, file_path, project_name, company_name
                FROM knowledge_chunks
                WHERE file_path IS NOT NULL
                ORDER BY created_at
            """)
        ).fetchall()

        total_chunks = len(rows)
        print(f"📊 Found {total_chunks} chunks with file paths")

        if total_chunks == 0:
            print("✅ No chunks to backfill!")
            return

        # Process each chunk
        updated_count = 0
        skipped_count = 0

        for row in rows:
            chunk_id = row.id
            file_path = row.file_path
            current_project_name = row.project_name
            current_company_name = row.company_name

            # Extract metadata from path
            new_project_name, new_company_name = extract_metadata_from_path(file_path)

            # Skip if already populated and correct
            if (current_project_name == new_project_name and
                current_company_name == new_company_name):
                skipped_count += 1
                continue

            # Update the chunk
            session.execute(
                text("""
                    UPDATE knowledge_chunks
                    SET project_name = :project_name,
                        company_name = :company_name,
                        updated_at = NOW()
                    WHERE id = :chunk_id
                """),
                {
                    "chunk_id": str(chunk_id),
                    "project_name": new_project_name,
                    "company_name": new_company_name,
                }
            )
            updated_count += 1

            # Log progress
            print(f"  ✓ Updated chunk {chunk_id}")
            print(f"    Path: {file_path}")
            print(f"    Metadata: project_name={new_project_name}, company_name={new_company_name}")

        # Commit all updates
        session.commit()

        # Summary
        print("\n" + "=" * 60)
        print("✅ BACKFILL COMPLETE!")
        print(f"  Total chunks: {total_chunks}")
        print(f"  Updated: {updated_count}")
        print(f"  Skipped (already correct): {skipped_count}")
        print("=" * 60)

        # Show breakdown by metadata type
        print("\n📊 Metadata breakdown:")
        stats = session.execute(
            text("""
                SELECT
                    CASE
                        WHEN project_name IS NOT NULL THEN 'Projects'
                        WHEN company_name IS NOT NULL THEN 'Experience'
                        WHEN source_type = 'personal_bio' THEN 'Personal'
                        ELSE 'Other'
                    END as category,
                    COUNT(*) as count
                FROM knowledge_chunks
                GROUP BY category
                ORDER BY count DESC
            """)
        ).fetchall()

        for stat in stats:
            print(f"  {stat.category}: {stat.count} chunks")

    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR during backfill: {e}")
        raise

    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 5.1 — Metadata Backfill Script")
    print("=" * 60)
    print()

    confirmation = input("This will update existing chunks. Continue? (yes/no): ")
    if confirmation.lower() != "yes":
        print("❌ Backfill cancelled.")
        sys.exit(0)

    print("\n🚀 Starting backfill...\n")
    backfill_metadata()
    print("\n✅ Done!\n")
