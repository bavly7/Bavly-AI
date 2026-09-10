"""
Phase 0 data population script.

Populates Supabase Postgres with:
  1. projects            (4 rows)
  2. certifications       (38 rows, file_url built from Supabase Storage)
  3. knowledge_chunks     (one row per .md file under knowledge/, with a
                           Cohere embedding generated from its content)

NEW: Each chunk now includes file_path and chunk_index for deterministic
     identification during GitHub webhook updates.

Run from the project root (D:\Gam3a\for_me\Portfolio):
    python scripts/populate_db.py

Requires in .env:
    DATABASE_URL=postgresql+psycopg2://...   (already set up)
    COHERE_API_KEY=...
"""

import os
import time
from pathlib import Path

import cohere
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Project, Certification, KnowledgeChunk

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
COHERE_API_KEY = os.environ["COHERE_API_KEY"]
SUPABASE_PROJECT_REF = "tqrzspriqldmywxncumf"
STORAGE_BUCKET = "certifications"

KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent / "knowledge"

co = cohere.Client(COHERE_API_KEY)
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def embed(text: str) -> list[float]:
    """Generate a single embedding via Cohere multilingual v3.0.
    input_type='search_document' is used for stored content (vs.
    'search_query' which we'll use later at retrieval time)."""
    resp = co.embed(
        texts=[text],
        model="embed-multilingual-v3.0",
        input_type="search_document",
    )
    return resp.embeddings[0]


def storage_url(filename: str) -> str:
    return (
        f"https://{SUPABASE_PROJECT_REF}.supabase.co/storage/v1/object/"
        f"public/{STORAGE_BUCKET}/{filename}"
    )


# ---------------------------------------------------------------------
# 1. PROJECTS
# ---------------------------------------------------------------------

PROJECTS = [
    {
        "name": "Automated KYC Onboarding System (Egyptian National ID)",
        "github_repo": "https://github.com/bavly7/Automated-KYC-Onboarding-System-Egyptian-National-ID",
        "tech_stack": ["LangGraph", "YOLO11", "PaddleOCR", "InsightFace", "MediaPipe", "FastAPI", "PostgreSQL"],
        "summary": "End-to-end identity-verification pipeline for Egyptian national IDs with automated approve/reject/manual-review/mobile-handoff decisions.",
        "folder": "kyc-onboarding",
    },
    {
        "name": "Agentic RAG Retail Analytics",
        "github_repo": "https://github.com/bavly7/Agentic-RAG-Retail-Assistant",
        "tech_stack": ["YOLO", "Llama-3", "LangChain", "LightGBM", "Qdrant", "OpenCV", "HuggingFace Embeddings"],
        "summary": "Retail analytics system combining live CV customer-behavior tracking, RAG documentation Q&A, and ML sales forecasting behind a conversational agent.",
        "folder": "agentic-rag-retail",
    },
    {
        "name": "Social Campaign Publisher",
        "github_repo": "https://github.com/bavly7/flyrank-capstone-social-studio",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Supabase", "SQLAlchemy", "Alembic", "Groq", "APScheduler", "OAuth 2.0"],
        "summary": "AI-powered social media campaign tool generating platform-specific captions and scheduling/publishing posts, with a real LinkedIn integration.",
        "folder": "social-media-publishing",
    },
    {
        "name": "PulseFit — AI-Powered Personal Trainer",
        "github_repo": "https://github.com/bavly7/Pulsefit",
        "tech_stack": ["Python", "Flask", "YOLO11-pose", "MediaPipe", "OpenCV", "Groq", "gTTS"],
        "summary": "Web-based AI gym coach with real-time pose-based rep counting and form correction, personalized workout generation, and Arabic/Franco-Arabic nutrition tracking.",
        "folder": "pulsefit",
    },
]


def insert_projects(session):
    project_id_by_folder = {}
    for p in PROJECTS:
        existing = session.query(Project).filter_by(name=p["name"]).first()
        if existing:
            project_id_by_folder[p["folder"]] = existing.id
            continue
        proj = Project(
            name=p["name"],
            folder_name=p["folder"],  # NEW: populate folder_name column
            github_repo=p["github_repo"],
            tech_stack=p["tech_stack"],
            summary=p["summary"],
        )
        session.add(proj)
        session.flush()  # get proj.id without committing yet
        project_id_by_folder[p["folder"]] = proj.id
        print(f"  + project: {p['name']}")
    session.commit()
    return project_id_by_folder


# ---------------------------------------------------------------------
# 2. CERTIFICATIONS
# ---------------------------------------------------------------------

CERTIFICATIONS = [
    ("AI Fundamentals", "Orange Digital Center Egypt", "Nov 2024", "AI Fundamentals", "Orange_Certification.pdf"),
    ("Machine Learning Internship", "Elevvo", "Aug-Sep 2025", "Machine Learning", "Machine_learning(Elevvo).pdf"),
    ("Deep Learning Certification", "NVIDIA", "2025", "Deep Learning", "Deep Learning (nvidia).pdf"),
    ("Associate Data Scientist", "DataCamp", "Oct 2025", "Data Science", "DATA SCIENTIST(DataCamp).pdf"),
    ("Computer Vision Trainee", "NTI / ITIDA", "Aug-Sep 2025", "Computer Vision", "Computer Vision (NTI_Itida).pdf"),
    ("CIB Internship Certificate", "Commercial International Bank (CIB)", None, "Banking Systems (theoretical internship)", "Bavly Waleed (CIB).pdf"),
    ("AI & Machine Learning Foundations", "Sprints AI", None, "AI / Machine Learning", "AI and Machine Learning Foundations(Sprints up).pdf"),
    ("Data Scientist Track", "DEPI", "Oct 2024 - May 2025", "Data Science", "AI & Data Science- Data Scientist(DEPI).pdf"),
    ("Agentic AI", "Oracle", None, "AI Agents", "Agentic AI Oracle.pdf"),
    ("Claude Code in Action", "Anthropic/Claude", None, "AI Tooling", "Claude Code in Action.pdf"),
    ("Claude Code 101", "Anthropic/Claude", None, "AI Tooling", "Claude Code 101.pdf"),
    ("Statistics in Python", "DataCamp", None, "Data Science", "Statistics in Python(DataCamp).pdf"),
    ("Python Toolbox", "DataCamp", None, "Python", "Python_toolbox(DataCamp).pdf"),
    ("Joining Data with pandas", "DataCamp", None, "Data Science", "Joining Data with pandas DataCamp.pdf"),
    ("Intermediate Python", "DataCamp", None, "Python", "Intermediate Python DataCamp.pdf"),
    ("Functions in Python", "DataCamp", None, "Python", "functions in python.pdf"),
    ("Data Visualization with Seaborn", "DataCamp", None, "Data Visualization", "Data Visualization with Seaborn(DataCamp).pdf"),
    ("Data Visualization with Matplotlib", "DataCamp", None, "Data Visualization", "Data Visualization with Matplotlib(DataCamp).pdf"),
    ("Data Manipulation with pandas", "DataCamp", None, "Data Science", "Data Manipulation with pandas DataCamp.pdf"),
    ("Transformers in Computer Vision", "ITI Mahara Tech", "2026", "Computer Vision", "Transformers In computer vision (Mahara - ITI).pdf"),
    ("Reinforcement Learning", "ITI Mahara Tech", "2026", "Reinforcement Learning", "Reinforcement Learning (Mahara_ITI).pdf"),
    ("TensorFlow 2 Sequential APIs Mastery", "ITI Mahara Tech", "2026", "Deep Learning / MLOps", "TensorFlow 2 Sequential APIs Mastery(ITI-Mahara).pdf"),
    ("Machine Learning for Data Scientists", "ITI Mahara Tech", "2026", "Machine Learning", "Machine learning for data scientist ITI(Mahara Tech).pdf"),
    ("PHP and MySQL", "ITI Mahara Tech", None, "Web Development", "PHP and MYSQL ITI(Mahara Tech).pdf"),
    ("Python Programming", "ITI Mahara Tech", None, "Python", "Python_programming ITI(Mahara).pdf"),
    ("Generative AI", "ITI Mahara Tech", "2026", "Generative AI", "Generative AI (ITI mahara tech).pdf"),
    ("Deployment of ML Models", "ITI Mahara Tech", "2026", "ML Deployment", "Deployment of ML models (ITI-MAHARA).pdf"),
    ("Deep Learning for Computer Vision", "ITI Mahara Tech", None, "Deep Learning / CV", "Deep Learning for computer vision(ITI_Mahara).pdf"),
    ("Deep Learning", "ITI Mahara Tech", None, "Deep Learning", "deep learning (ITI).pdf"),
    ("Computer Vision Engineer", "ITI Mahara Tech", "2026", "Computer Vision", "Computer Vision Engineer.pdf"),
    ("Computer Vision Engineer (Arabic)", "ITI Mahara Tech", "2026", "Computer Vision", "Computer Vision Engineer (Arabic).pdf"),
    ("AI For Everyone", "DeepLearning.AI (Andrew Ng)", None, "AI Fundamentals", "AI For everyone.pdf"),
    ("Computer Vision Applications", "ITI Mahara Tech", None, "Computer Vision", "Computer Vision Applications(ITI Mahara).pdf"),
]


def insert_certifications(session):
    for title, issuer, date, field, filename in CERTIFICATIONS:
        existing = session.query(Certification).filter_by(title=title, issuer=issuer).first()
        if existing:
            continue
        cert = Certification(
            title=title,
            issuer=issuer,
            date=date,
            field=field,
            file_url=storage_url(filename),
        )
        session.add(cert)
        print(f"  + cert: {title} ({issuer})")
    session.commit()


# ---------------------------------------------------------------------
# 3. KNOWLEDGE CHUNKS (from .md files)
# ---------------------------------------------------------------------
# Maps a folder under knowledge/ to a source_type.
# personal/*.md          -> personal_bio
# experience/*/*.md      -> experience
# projects/*/*.md        -> project_narrative  (except github_metadata.md -> github_readme)


def detect_language(text: str) -> str:
    """Very rough heuristic: if the text contains a good number of Arabic
    characters, tag it ar-EG, otherwise en. Since all current content is
    English, this will tag everything 'en' for now — refine later if
    Arabic-authored content is added directly instead of translated at
    generation time."""
    arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
    return "ar-EG" if arabic_chars > 20 else "en"


def insert_knowledge_chunks(session, project_id_by_folder):
    # personal/
    personal_dir = KNOWLEDGE_ROOT / "personal"
    for md_file in sorted(personal_dir.glob("*.md")):
        _insert_chunk(session, md_file, source_type="personal_bio", project_id=None)

    # experience/<company>/*.md
    experience_dir = KNOWLEDGE_ROOT / "experience"
    for company_dir in sorted(experience_dir.iterdir()):
        if not company_dir.is_dir():
            continue
        for md_file in sorted(company_dir.glob("*.md")):
            _insert_chunk(session, md_file, source_type="experience", project_id=None)

    # projects/<project>/*.md
    projects_dir = KNOWLEDGE_ROOT / "projects"
    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        folder_name = project_dir.name
        project_id = project_id_by_folder.get(folder_name)
        if project_id is None:
            print(f"  ! WARNING: no matching project_id for folder '{folder_name}', skipping its files")
            continue
        for md_file in sorted(project_dir.glob("*.md")):
            source_type = "github_readme" if md_file.stem == "github_metadata" else "project_narrative"
            _insert_chunk(session, md_file, source_type=source_type, project_id=project_id)

    session.commit()


def _insert_chunk(session, md_file: Path, source_type: str, project_id):
    """
    Insert a chunk for the given markdown file.

    Now uses file_path + chunk_index as the unique identifier:
    - If a chunk with that file_path already exists, DELETE it first (update scenario)
    - Then insert the new chunk with the current content and embedding
    """
    content = md_file.read_text(encoding="utf-8").strip()
    if not content:
        return

    # Skip files that are still just placeholders (e.g. RPA not started)
    if content.startswith("<!--") and content.endswith("-->") and len(content) < 500:
        print(f"  - skipping placeholder-only file: {md_file}")
        return

    # Build the file_path relative to knowledge/ root
    file_path = str(md_file.relative_to(KNOWLEDGE_ROOT)).replace("\\", "/")

    # For now, each file = one chunk, so chunk_index is always 0
    # In the future, if we split files into multiple chunks, this will increment
    chunk_index = 0

    # Check if a chunk with this file_path already exists
    existing = session.query(KnowledgeChunk).filter_by(file_path=file_path).first()
    if existing:
        # Content unchanged? Skip re-embedding (saves API calls)
        if existing.content == content:
            print(f"  = chunk unchanged: {file_path}")
            return
        # Content changed? Delete old chunk, will re-insert below
        session.delete(existing)
        print(f"  ~ chunk updated: {file_path}")

    language = detect_language(content)
    vector = embed(content)

    chunk = KnowledgeChunk(
        source_type=source_type,
        project_id=project_id,
        content=content,
        embedding=vector,
        language=language,
        file_path=file_path,
        chunk_index=chunk_index,
    )
    session.add(chunk)
    print(f"  + chunk: {file_path}  ({source_type})")

    # Cohere free tier is rate-limited; small delay keeps us safely under it
    time.sleep(0.3)


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main():
    session = Session()
    try:
        print("Inserting projects...")
        project_id_by_folder = insert_projects(session)

        print("\nInserting certifications...")
        insert_certifications(session)

        print("\nInserting knowledge chunks (this calls Cohere per file, may take a bit)...")
        insert_knowledge_chunks(session, project_id_by_folder)

        print("\nDone.")
    finally:
        session.close()


if __name__ == "__main__":
    main()