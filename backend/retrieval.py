"""
Phase 1 — Retrieval (Refactored for Phase 5.1 Multi-Entity Support)

Given a user question, this module:
  1. Embeds the query (Cohere, input_type='search_query')
  2. Runs cosine-similarity search against knowledge_chunks (pgvector)
     with optional single-entity metadata pre-filtering
  3. Supports tech filters via content ILIKE search
  4. Optionally does structured lookups against certifications

Key Changes in Phase 5.1:
- search_knowledge_chunks now accepts single-entity filters
- Tech filters use OR-based content matching
- Designed to be called in parallel for multi-entity queries
"""

import os
import time
from dataclasses import dataclass
from typing import List, Optional

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
CONFIDENCE_THRESHOLD = 0.25

TOP_K = 5


@dataclass
class RetrievedChunk:
    content: str
    source_type: str
    project_id: str | None
    similarity: float
    # Additional metadata for debugging
    project_name: str | None = None
    company_name: str | None = None


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
    limit: int = TOP_K,
    company_name: Optional[str] = None,
    project_name: Optional[str] = None,
    source_type: Optional[str] = None,
    tech_filters: Optional[List[str]] = None,
) -> list[RetrievedChunk]:
    """
    Vector similarity search over knowledge_chunks with single-entity metadata pre-filtering.

    Phase 5.1: Designed to be called in parallel for multi-entity queries.
    Each call filters by ONE entity (one company OR one project OR one source_type).

    Args:
        query: User's question text
        limit: Number of results to return (use 2-3 for multi-entity parallel calls)
        company_name: Single company to filter by (e.g., "elevvo")
        project_name: Single project to filter by (e.g., "kyc")
        source_type: Single source type to filter by (e.g., "personal_bio")
        tech_filters: List of technologies to search for in content (OR logic)

    Returns:
        List of RetrievedChunk objects sorted by similarity

    Uses pgvector's cosine distance operator (<=>); similarity = 1 - distance.

    Example Usage:
        # Single entity search
        chunks = search_knowledge_chunks("Tell me about the project", project_name="kyc", limit=3)

        # Multi-entity search (call in parallel)
        kyc_chunks = search_knowledge_chunks(query, project_name="kyc", limit=2)
        pulsefit_chunks = search_knowledge_chunks(query, project_name="pulsefit", limit=2)
        all_chunks = kyc_chunks + pulsefit_chunks
    """
    query_embedding = embed_query(query)

    # Build WHERE clause conditions
    where_conditions = []
    params = {"query_embedding": str(query_embedding), "limit": limit}

    # Single-entity filters (mutually exclusive by design)
    if company_name:
        where_conditions.append("LOWER(company_name) = LOWER(:company_name)")
        params["company_name"] = company_name

    if project_name:
        where_conditions.append("LOWER(project_name) = LOWER(:project_name)")
        params["project_name"] = project_name

    if source_type:
        where_conditions.append("source_type = :source_type")
        params["source_type"] = source_type

    # Tech filters: OR-based content search
    # Example: (content ILIKE '%yolo%' OR content ILIKE '%langraph%')
    if tech_filters and len(tech_filters) > 0:
        tech_conditions = []
        for idx, tech in enumerate(tech_filters):
            tech_param = f"tech_{idx}"
            tech_conditions.append(f"content ILIKE :{tech_param}")
            params[tech_param] = f"%{tech}%"
        where_conditions.append(f"({' OR '.join(tech_conditions)})")

    # Combine all conditions with AND
    where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"

    sql = text(f"""
        SELECT
            content,
            source_type,
            project_id,
            project_name,
            company_name,
            1 - (embedding <=> :query_embedding) AS similarity
        FROM knowledge_chunks
        WHERE {where_clause}
        ORDER BY embedding <=> :query_embedding
        LIMIT :limit
    """)

    try:
        with engine.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
    except Exception as e:
        print(f"⚠️ SQL Error in search_knowledge_chunks: {e}")
        print(f"   Query: {query[:100]}...")
        print(f"   Filters: company={company_name}, project={project_name}, source={source_type}, tech={tech_filters}")
        return []

    return [
        RetrievedChunk(
            content=row.content,
            source_type=row.source_type,
            project_id=str(row.project_id) if row.project_id else None,
            similarity=row.similarity,
            project_name=row.project_name,
            company_name=row.company_name,
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


def find_projects_by_tech(
    technologies: list[str],
    limit: int = 3
) -> list[tuple[str, str, list[str]]]:
    """
    Find projects that use ANY of the given technologies.

    Args:
        technologies: List of tech keywords (e.g., ["OCR", "ByteTrack"])
        limit: Maximum number of projects to return (default 3)

    Returns:
        List of (folder_name, display_name, tech_stack) tuples,
        ranked by number of matching technologies

    Example:
        >>> find_projects_by_tech(["YOLO", "Computer Vision"], limit=3)
        [
            ("agentic-rag-retail", "Agentic RAG Retail", ["YOLO", "Qdrant", ...]),
            ("pulsefit", "PulseFit", ["YOLO", "ByteTrack", ...])
        ]
    """
    if not technologies:
        return []

    with engine.connect() as conn:
        # Build ILIKE patterns for each technology
        tech_conditions = []
        params = {"limit": limit}

        for idx, tech in enumerate(technologies):
            param_name = f"tech_{idx}"
            # Check if ANY element in tech_stack array matches this technology
            tech_conditions.append(
                f"EXISTS (SELECT 1 FROM unnest(tech_stack) t WHERE t ILIKE :{param_name})"
            )
            params[param_name] = f"%{tech}%"

        where_clause = " OR ".join(tech_conditions) if tech_conditions else "FALSE"

        # Build match count expression
        match_expressions = [f"t ILIKE :{f'tech_{i}'}" for i in range(len(technologies))]
        match_count_expr = " OR ".join(match_expressions) if match_expressions else "FALSE"

        sql = text(f"""
            SELECT
                folder_name,
                name AS display_name,
                tech_stack,
                -- Count how many technologies match (for relevance ranking)
                (
                    SELECT COUNT(DISTINCT t)
                    FROM unnest(tech_stack) t
                    WHERE {match_count_expr}
                ) AS match_count
            FROM projects
            WHERE {where_clause}
            ORDER BY match_count DESC, name ASC
            LIMIT :limit
        """)

        try:
            rows = conn.execute(sql, params).fetchall()
            return [
                (row.folder_name, row.display_name, row.tech_stack or [])
                for row in rows
            ]
        except Exception as e:
            print(f"⚠️ Error in find_projects_by_tech: {e}")
            return []


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
    """Main retrieval entrypoint used by the generation step (legacy Phase 1 interface).

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
    test_query = "what achievement bavly had at DEPI training?"
    result = retrieve(test_query)
    print(f"Query: {test_query}")
    print(f"Confident: {result['confident']}")
    for c in result["chunks"]:
        print(f"  [{c.similarity:.3f}] ({c.source_type}) {c.content[:100]}...")