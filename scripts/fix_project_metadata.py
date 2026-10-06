"""
One-time migration: Fix truncated project_name values in knowledge_chunks.

Current bug: project_name = folder_name.split("-")[0]
  "skin-cancer-gan-augmentation" → "skin"
  "agentic-rag-retail" → "agentic"

Fix: project_name = folder_name (full folder name)
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

print("🔧 Starting project metadata fix...")

with engine.begin() as conn:
    # Fix project_name: Extract full folder name from file_path
    result = conn.execute(text("""
        UPDATE knowledge_chunks
        SET project_name = split_part(file_path, '/', 2)
        WHERE source_type IN ('project_narrative', 'github_readme')
          AND file_path LIKE 'projects/%'
          AND project_name IS NOT NULL
    """))

    print(f"✅ Fixed {result.rowcount} project_name values")

    # Verify the fix
    rows = conn.execute(text("""
        SELECT DISTINCT project_name, file_path
        FROM knowledge_chunks
        WHERE source_type IN ('project_narrative', 'github_readme')
        ORDER BY project_name
    """)).fetchall()

    print("\n📋 Current project names in database:")
    for row in rows:
        print(f"  {row.project_name} (from {row.file_path})")

    print("\n✅ Project metadata fix complete!")
