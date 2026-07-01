"""
Resume Analyzer

Extracts skills from a resume PDF, compares against a JD's skill list,
and outputs a gap analysis with match score.

PII Handling: Resume text is processed in-memory only — never persisted
to database or logs. This is an intentional guardrail.
"""

import os
import json
import fitz  # pymupdf
from pathlib import Path
from typing import Optional
from loguru import logger

from backend.config import settings
from backend.db.mongo_store import structured_store
from backend.rag.retriever import hybrid_retrieve


def _get_llm():
    """Lazy-load the Gemini LLM."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        temperature=0.1,
    )


EXTRACT_SKILLS_PROMPT = """You are a skill extraction expert. Extract all technical and professional skills from the following {doc_type} text.

Return a JSON object with:
- skills: List of skill names (normalize to standard names, e.g., "Structured Query Language" → "SQL", "Machine Learning" → "ML")
- experience_level: For each skill, estimate the level if possible ("beginner", "intermediate", "advanced"). If not determinable, use "unknown".

Return format:
{{"skills": ["SQL", "Python", "React", ...], "skill_details": [{{"skill": "SQL", "level": "intermediate"}}, ...]}}

{doc_type} Text:
{text}

JSON Output:"""


GAP_ANALYSIS_PROMPT = """You are a career advisor. Given a candidate's skills and a job description's required skills, provide a detailed gap analysis.

Candidate Skills: {resume_skills}
JD Required Skills: {jd_skills}
Company: {company}
Role: {role}

Provide:
1. A match score (percentage of JD skills found in resume)
2. Matched skills (skills present in both)
3. Missing skills (in JD but not in resume) — rank by importance
4. Extra skills (in resume but not in JD) — note which ones are still valuable
5. Brief recommendations for the top 3 missing skills

Return as JSON:
{{"match_score": 76, "matched_skills": [...], "missing_skills": [...], "extra_skills": [...], "recommendations": [...]}}

JSON Output:"""


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract text from a PDF file. Returns combined text from all pages."""
    pdf_path = Path(pdf_path)
    text_parts = []
    pdf = fitz.open(str(pdf_path))
    for page in pdf:
        text_parts.append(page.get_text("text"))
    pdf.close()
    return "\n".join(text_parts)


def extract_text_from_bytes(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes (for uploaded files)."""
    pdf = fitz.open(stream=pdf_bytes, filetype="pdf")
    text_parts = []
    for page in pdf:
        text_parts.append(page.get_text("text"))
    pdf.close()
    return "\n".join(text_parts)


def extract_skills(text: str, doc_type: str = "resume") -> dict:
    """
    Extract skills from text using LLM.

    Args:
        text: Resume or JD text
        doc_type: "resume" or "job description"

    Returns:
        Dict with 'skills' list and 'skill_details' list
    """
    llm = _get_llm()

    # Truncate if too long (keep first 4000 chars for context window efficiency)
    truncated = text[:4000] if len(text) > 4000 else text

    prompt = EXTRACT_SKILLS_PROMPT.format(doc_type=doc_type, text=truncated)

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        return json.loads(content)
    except Exception as e:
        logger.error(f"Skill extraction failed: {e}")
        return {"skills": [], "skill_details": []}


def get_jd_skills(company: str) -> dict:
    """
    Get required skills for a company from:
    1. Structured store (if company info exists)
    2. RAG retrieval from JD documents
    """
    # Try structured store first
    company_info = structured_store.find_one("companies", {"company": company})
    if company_info and company_info.get("skills"):
        return {
            "skills": company_info["skills"],
            "role": company_info.get("role", "Not specified"),
            "source": "structured_store",
        }

    # Fall back to RAG retrieval from JD chunks
    chunks = hybrid_retrieve(
        query=f"Required skills and qualifications for {company}",
        company=company,
        doc_type="job_description",
        top_k=5,
    )

    if chunks:
        # Extract skills from retrieved JD chunks
        combined_text = "\n".join(c["text"] for c in chunks)
        extracted = extract_skills(combined_text, doc_type="job description")
        return {
            "skills": extracted.get("skills", []),
            "role": "Not specified",
            "source": "rag_retrieval",
        }

    return {"skills": [], "role": "Not specified", "source": "not_found"}


def analyze_resume(
    resume_text: str,
    company: str,
    resume_pdf_bytes: Optional[bytes] = None,
) -> dict:
    """
    Full resume analysis pipeline.

    Args:
        resume_text: Resume text (or empty if pdf_bytes provided)
        company: Target company name
        resume_pdf_bytes: Raw PDF bytes (if text not pre-extracted)

    Returns:
        Analysis dict with match_score, matched/missing/extra skills,
        and recommendations. Resume text is NOT persisted anywhere.
    """
    # Extract text from PDF bytes if needed
    if resume_pdf_bytes and not resume_text:
        resume_text = extract_text_from_bytes(resume_pdf_bytes)

    if not resume_text.strip():
        return {"error": "No text could be extracted from the resume."}

    # NOTE: resume_text is only used in-memory — never logged or stored
    logger.info(f"Analyzing resume against {company} (text length: {len(resume_text)} chars)")

    # Step 1: Extract resume skills
    resume_extracted = extract_skills(resume_text, doc_type="resume")
    resume_skills = set(s.lower() for s in resume_extracted.get("skills", []))

    # Step 2: Get JD skills for the target company
    jd_info = get_jd_skills(company)
    jd_skills = set(s.lower() for s in jd_info.get("skills", []))

    if not jd_skills:
        return {
            "error": f"No job description or skills data found for {company}. Please ingest JD documents first.",
            "resume_skills": sorted(resume_extracted.get("skills", [])),
        }

    # Step 3: Compute gap analysis
    matched = resume_skills & jd_skills
    missing = jd_skills - resume_skills
    extra = resume_skills - jd_skills
    match_score = round(len(matched) / len(jd_skills) * 100, 1) if jd_skills else 0

    # Step 4: Get LLM-generated recommendations
    try:
        llm = _get_llm()
        prompt = GAP_ANALYSIS_PROMPT.format(
            resume_skills=sorted(resume_extracted.get("skills", [])),
            jd_skills=sorted(jd_info.get("skills", [])),
            company=company,
            role=jd_info.get("role", "Not specified"),
        )
        response = llm.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        llm_analysis = json.loads(content)
        recommendations = llm_analysis.get("recommendations", [])
    except Exception as e:
        logger.warning(f"LLM gap analysis failed, using basic analysis: {e}")
        recommendations = [
            f"Study {skill} — required by {company}" for skill in sorted(missing)[:3]
        ]

    result = {
        "company": company,
        "role": jd_info.get("role", "Not specified"),
        "match_score": match_score,
        "matched_skills": sorted(s.title() for s in matched),
        "missing_skills": sorted(s.title() for s in missing),
        "extra_skills": sorted(s.title() for s in extra),
        "resume_skills_count": len(resume_skills),
        "jd_skills_count": len(jd_skills),
        "recommendations": recommendations,
        "jd_source": jd_info.get("source", "unknown"),
    }

    logger.info(
        f"Resume analysis complete: match_score={match_score}%, "
        f"matched={len(matched)}, missing={len(missing)}"
    )

    return result
