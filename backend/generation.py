"""
Phase 1 — Generation

Given a user question + the retrieval() output from retrieval.py, this
module produces a grounded natural-language answer, with:

  - Explicit refusal fallback when retrieval confidence is too low
    (RULES.md #1, #2, #5 — never guess or extrapolate).
  - A separate `certificate_links` structured field when the question is
    certification-related (SPECS.md §8 — never embed raw URLs in prose).
  - A separate `profile_links` structured field when the question asks
    for the owner's external profiles (GitHub / LinkedIn / Kaggle) — same
    pattern as certificate_links: structured lookup, not LLM-generated,
    so a link can never be hallucinated or mistyped by the model.

Language: responds in Egyptian Arabic colloquial for Arabic input, English
otherwise (RULES.md #16). Tone tagging is deferred to Phase 6 (SPECS.md
build order) and is NOT implemented here.
"""

import os
import re

from dotenv import load_dotenv
from groq import Groq

from backend.retrieval import RetrievedChunk, retrieve
from backend.retrieval import looks_like_certification_question

load_dotenv()

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")  # default to a smaller, cheaper model if not set

client = Groq(api_key=GROQ_API_KEY)

# Structured lookup — hardcoded, never LLM-generated. Same principle as
# get_certifications() in retrieval.py: a direct, trusted data source, not
# something the model is allowed to guess or reconstruct.
PROFILE_LINKS = [
    {"platform": "LinkedIn", "url": "https://www.linkedin.com/in/bavly-waleed"},
    {"platform": "Kaggle", "url": "https://www.kaggle.com/bavlywaleed"},
    {"platform": "GitHub", "url": "https://github.com/bavly7"},
]

FALLBACK_MESSAGES = {
    "ar": "معلش، مش لاقي معلومة كافية عن الموضوع ده حاليًا.",
    "en": "I don't have enough information about that yet.",
}

# Cheap keyword check for Phase 1 (linear, no intent classifier yet — real
# classify_intent node comes in Phase 2 per SPECS.md §4/§12).
PROFILE_LINK_KEYWORDS = [
    "linkedin", "github", "kaggle", "profile", "portfolio",
    "social", "contact", "لينكد", "جيت هب", "كاجل", "بروفايل",
]

# Basic Arabic-script detection — good enough for Phase 1 language routing.
ARABIC_RE = re.compile(r"[\u0600-\u06FF]")


def detect_language(query: str) -> str:
    return "ar" if ARABIC_RE.search(query) else "en"


def looks_like_profile_link_question(query: str) -> bool:
    q_lower = query.lower()
    return any(k in q_lower for k in PROFILE_LINK_KEYWORDS)

#chunks is a list from retriever then make it into one string to be used in the prompt
def _format_context(chunks: list[RetrievedChunk]) -> str:
    """Turns retrieved chunks into a labeled context block for the prompt,
    so generation can be checked against exactly what was retrieved."""
    lines = []
    for i, c in enumerate(chunks, start=1):
        lines.append(f"[{i}] (source_type={c.source_type}) {c.content}")
    return "\n".join(lines)


def _build_system_prompt(language: str) -> str:
    lang_instruction = (
        "Respond in Egyptian Arabic colloquial (not Modern Standard Arabic)."
        if language == "ar"
        else "Respond in English."
    )
    return (
        "You are Bavly, an AI portfolio assistant representing Bavly Waleed, "
        "a Computer Vision/ML engineer/AI engineer, speaking to a recruiter.\n\n"
        "STRICT RULES:\n"
        "- Only state facts that are explicitly present in the CONTEXT block below.\n"
        "- Never invent, infer, or extrapolate personal/project/certification facts "
        "not present in CONTEXT.\n"
        "- If CONTEXT does not contain enough information to answer, say so plainly "
        "instead of guessing.\n"
        "- Do not include raw URLs in your answer text — links are attached separately.\n"
        "- General knowledge questions not about the owner may be answered normally, "
        "but must never be blended with or presented as the owner's personal experience.\n"
        f"- {lang_instruction}"
    )


def generate(query: str) -> dict:
    language = detect_language(query)
    result = retrieve(query)

    certificate_links = (
    [
        {"title": c["title"], "issuer": c["issuer"], "url": c["file_url"]}
        for c in result["certifications"]
    ]
    if looks_like_certification_question(query)
    else []
)

    profile_links = PROFILE_LINKS if looks_like_profile_link_question(query) else []


    cert_text = ""
    if certificate_links:
        cert_text = "\nCERTIFICATIONS FOUND IN DATABASE:\n" + "\n".join(
            f"- {c['title']} by {c['issuer']}" for c in certificate_links
        )


    profile_text = ""
    if profile_links:
        profile_text = "\nOWNER PROFILES:\n" + "\n".join(
            f"- {p['platform']}: {p['url']}" for p in profile_links
        )

    chunks = result["chunks"] if result["confident"] else []
    context = _format_context(chunks) if chunks else "(no additional context retrieved)"

    system_prompt = _build_system_prompt(language)
    

    user_prompt = f"CONTEXT:\n{context}{cert_text}{profile_text}\n\nQUESTION:\n{query}"

    if chunks or certificate_links or profile_links:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        answer = response.choices[0].message.content.strip()
    else:
        answer = FALLBACK_MESSAGES[language]

    sources = sorted({c.source_type for c in chunks})

    return {
        "answer": answer,
        "sources": sources,
        "certificate_links": certificate_links,
        "profile_links": profile_links,
    }


if __name__ == "__main__":
    # Quick manual tests — run directly: python generation.py
    test_queries = [
        # "what is tech stacks bavly used in Social media campaigns project? and tell me about the project",
        # "what certifications does bavly have in computer vision?",
        # "where can I find your github or linkedin?",
        "ايه شهادات بافلي في الرؤية الحاسوبية؟",
        # "what's bavly's favorite color?",
        # "introduce yourself who is bavly waleed?",
        # "what role of bavly in flyrank internship?",
    ]
    for q in test_queries:
        result = generate(q)
        print(f"\nQ: {q}")
        print(f"A: {result['answer']}")
        print(f"sources={result['sources']}")
        print(f"certificate_links={result['certificate_links']}")
        print(f"profile_links={result['profile_links']}")