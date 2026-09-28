"""
Phase 1 — Retrieval

Given a user question, this module:
  1. Embeds the query (Cohere, input_type='search_query')
  2. Runs cosine-similarity search against knowledge_chunks (pgvector)
  3. Optionally does structured lookups against certifications / projects
     when the question is clearly about those (simple keyword routing for
     now — real intent classification comes when we port to LangGraph in
     Phase 2)

Returns a list of retrieved chunks with their similarity scores, so the
generation step can decide whether confidence is high enough to answer.
"""

import os
import time
from dataclasses import dataclass

import cohere
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
COHERE_API_KEY = os.environ["COHERE_API_KEY"]

co = cohere.Client(COHERE_API_KEY)
engine = create_engine(DATABASE_URL)

# Below this cosine similarity score, a chunk is considered too weak to
# trust. Cosine similarity here ranges roughly 0-1 for normalized
# embeddings; this threshold is a starting point, not calibrated against
# a labeled eval set yet — same honest caveat as the KYC project's
# thresholds. Revisit once we've tested against real questions.
CONFIDENCE_THRESHOLD = 0.35

TOP_K = 5


@dataclass
class RetrievedChunk:
    content: str
    source_type: str
    project_id: str | None
    similarity: float


def embed_query(text: str) -> list[float]:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            resp = co.embed(
                texts=[text],
                model="embed-multilingual-v3.0",
                input_type="search_query",
            )
            return resp.embeddings[0]
        except Exception as e:
            print(f"Cohere API Error (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)


def search_knowledge_chunks(
    query: str,
    top_k: int = TOP_K,
    project_names: list[str] | None = None,
    company_names: list[str] | None = None,
    include_personal: bool = False,
) -> list[RetrievedChunk]:
    """
    Vector similarity search over knowledge_chunks with mixed metadata pre-filtering.

    Phase 5.1 Mixed Filters: Supports multiple projects, companies, and personal in ONE query.
    Uses OR conditions to combine filters, allowing queries like:
    - "Compare KYC and PulseFit" → projects OR
    - "Tell me about Elevvo and FlyRank" → companies OR
    - "Your skills and work at Elevvo" → personal OR company
    - "Compare KYC project vs Elevvo experience" → project OR company

    Args:
        query: User's question text
        top_k: Number of results to return
        project_names: List of projects to filter by (e.g., ["kyc", "pulsefit"])
        company_names: List of companies to filter by (e.g., ["elevvo", "flyrank"])
        include_personal: Whether to include personal_bio chunks (for mixed queries)

    Returns:
        List of RetrievedChunk objects sorted by similarity

    Uses pgvector's cosine distance operator (<=>); similarity = 1 - distance.
    """
    query_embedding = embed_query(query)

    # Build OR conditions for mixed filtering
    or_conditions = []
    params = {"query_embedding": str(query_embedding), "top_k": top_k}

    # Add project filters (supports multiple projects)
    if project_names:
        if len(project_names) == 1:
            or_conditions.append("project_name = :project_0")
            params["project_0"] = project_names[0].lower()
        else:
            # Multiple projects: "project_name IN ('kyc', 'pulsefit')"
            placeholders = ", ".join([f":project_{i}" for i in range(len(project_names))])
            or_conditions.append(f"project_name IN ({placeholders})")
            for i, project in enumerate(project_names):
                params[f"project_{i}"] = project.lower()

    # Add company filters (supports multiple companies)
    if company_names:
        if len(company_names) == 1:
            or_conditions.append("company_name = :company_0")
            params["company_0"] = company_names[0].lower()
        else:
            # Multiple companies: "company_name IN ('elevvo', 'flyrank')"
            placeholders = ", ".join([f":company_{i}" for i in range(len(company_names))])
            or_conditions.append(f"company_name IN ({placeholders})")
            for i, company in enumerate(company_names):
                params[f"company_{i}"] = company.lower()

    # Add personal filter if requested
    if include_personal:
        or_conditions.append("source_type = 'personal_bio'")

    # Construct WHERE clause with OR logic
    # If no filters specified, search all chunks (fallback)
    where_clause = " OR ".join(or_conditions) if or_conditions else "TRUE"

    sql = text(f"""
        SELECT
            content,
            source_type,
            project_id,
            1 - (embedding <=> :query_embedding) AS similarity
        FROM knowledge_chunks
        WHERE {where_clause}
        ORDER BY embedding <=> :query_embedding
        LIMIT :top_k
    """)

    with engine.connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [
        RetrievedChunk(
            content=row.content,
            source_type=row.source_type,
            project_id=str(row.project_id) if row.project_id else None,
            similarity=row.similarity,
        )
        for row in rows
    ]


def looks_like_certification_question(query: str) -> bool:
    keywords = [
        "certification", "certificate", "cert", "course", "training",
        "شهادة", "شهادات", "دورة", "كورسات",
    ]
    q_lower = query.lower()
    return any(k in q_lower for k in keywords)


# Simple keyword -> field-column value mapping for Phase 1 (RULES.md #15:
# no extra LLM classification round trip yet — that's Phase 2's
# classify_intent job). Extend this map as new cert `field` values are
# added to the certifications table, so it stays a direct reflection of
# the data rather than a guess.
CERT_FIELD_KEYWORDS = {
    "computer vision": [
        "computer vision", "cv",
        "حاسوبية", "الحاسوبية", "حاسوبيه", "الحاسوبيه",  # matches with/without "ال" prefix
    ],
    "machine learning": ["machine learning", "ml", "تعلم الآلة", "تعلم الالة", "الآلة", "الالة"],
    "deep learning": ["deep learning", "تعلم عميق", "العميق"],
    "data science": ["data science", "data scientist", "علم البيانات", "البيانات"],
    "nlp": ["nlp", "natural language processing", "معالجة اللغات", "اللغات"],
    "generative ai": ["generative ai", "gen ai", "توليدي", "التوليدي"],
    "agentic ai": ["agentic ai", "ai agents", "agent"],
}


def extract_cert_field_filter(query: str) -> str | None:
    """Cheap keyword match against known certification field values.
    Returns the canonical field string to filter on, or None if the
    query doesn't name a specific domain (in which case all certs are
    returned, same as before)."""
    q_lower = query.lower()
    for canonical_field, keywords in CERT_FIELD_KEYWORDS.items():
        if any(k in q_lower for k in keywords):
            return canonical_field
    return None


def get_certifications(field_filter=None):
    with engine.connect() as conn:
        if field_filter:
    
            query = text("""
                SELECT title, issuer, file_url FROM certifications 
                WHERE LOWER(title) LIKE LOWER(:flt) 
                   OR LOWER(issuer) LIKE LOWER(:flt)
            """)
            rows = conn.execute(query, {"flt": f"%{field_filter}%"}).fetchall()
        else:
        
            query = text("SELECT title, issuer, file_url FROM certifications")
            rows = conn.execute(query).fetchall()
            
    return [{"title": r.title, "issuer": r.issuer, "file_url": r.file_url} for r in rows]


def retrieve(query: str) -> dict:
    """Main retrieval entrypoint used by the generation step.

    Returns a dict with:
      - chunks: list of RetrievedChunk, sorted by similarity desc
      - confident: bool, whether the top result clears CONFIDENCE_THRESHOLD
      - certifications: list of cert dicts, only populated if the query
        looks certification-related (cheap keyword check for now).
        Filtered by field when the query names a specific domain (e.g.
        "computer vision certifications" only returns CV certs, not all
        of them) — falls back to unfiltered if no domain keyword matches,
        same as before.
    """
    chunks = search_knowledge_chunks(query)
    confident = bool(chunks) and chunks[0].similarity >= CONFIDENCE_THRESHOLD

    certifications = []
    if looks_like_certification_question(query):
        field_filter = extract_cert_field_filter(query)
        certifications = get_certifications(field_filter=field_filter)

    return {
        "chunks": chunks,
        "confident": confident,
        "certifications": certifications,
    }


if __name__ == "__main__":
    # Quick manual test — run directly: python retrieval.py
    test_query = "what achivemnet bavly had at DEPI training?"
    result = retrieve(test_query)
    print(f"Query: {test_query}")
    print(f"Confident: {result['confident']}")
    for c in result["chunks"]:
        print(f"  [{c.similarity:.3f}] ({c.source_type}) {c.content[:100]}...")