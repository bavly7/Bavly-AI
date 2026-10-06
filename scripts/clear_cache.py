"""
Clear answer cache after knowledge base changes.
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

print("🗑️  Clearing answer cache...")

with engine.begin() as conn:
    deleted = conn.execute(text("DELETE FROM answer_cache")).rowcount
    print(f"✅ Cleared {deleted} cached answer(s)")

print("\n✅ Cache cleared successfully!")
