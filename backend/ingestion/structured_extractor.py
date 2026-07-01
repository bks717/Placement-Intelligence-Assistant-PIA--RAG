"""
Structured Extractor

Uses Gemini LLM to extract structured data from interview experience
and JD chunks. Stores extracted records in the structured data store.

Extracts:
- Interview questions with round, difficulty, topic tags
- Company metadata (package, role, skills)
"""

import json
import os
from loguru import logger

from backend.config import settings
from backend.ingestion.pdf_loader import Document
from backend.db.mongo_store import structured_store


def _get_llm():
    """Lazy-load the Gemini LLM."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        temperature=0.1,  # Low temp for extraction
    )


EXTRACT_QUESTIONS_PROMPT = """You are a structured data extractor. Given text from an interview experience document, extract all interview questions mentioned.

For each question, provide:
- question: The actual question text
- round: The interview round (e.g., "Technical", "HR", "Aptitude", "Coding", "Online Assessment", "Group Discussion"). If not clear, use "Unknown".
- difficulty: Estimated difficulty ("Easy", "Medium", "Hard"). If not clear, use "Medium".
- topic: The topic/category (e.g., "SQL", "Python", "DSA", "DBMS", "Statistics", "Aptitude", "System Design", "Behavioral", "OS", "Networking"). If not clear, use "General".

Return a JSON array of objects. If no questions are found, return an empty array [].

IMPORTANT: Only extract actual interview questions. Do not fabricate or add questions that aren't in the text.

Text:
{text}

JSON Output:"""


EXTRACT_COMPANY_PROMPT = """You are a structured data extractor. Given text from an interview experience or job description document for company "{company}", extract company metadata.

Provide:
- company: Company name
- package: Salary/CTC if mentioned (e.g., "16 LPA", "12-15 LPA"). Use "Not mentioned" if not found.
- role: Job role/position if mentioned. Use "Not mentioned" if not found.
- skills: List of required/tested skills mentioned (e.g., ["SQL", "Python", "Statistics"])
- rounds: List of interview rounds mentioned (e.g., ["Online Assessment", "Technical", "HR"])
- eligibility: Eligibility criteria if mentioned. Use "Not mentioned" if not found.

Return a single JSON object.

Text:
{text}

JSON Output:"""


def extract_questions_from_chunk(chunk: Document) -> list[dict]:
    """
    Extract structured questions from a single chunk using LLM.

    Returns list of question dicts with metadata from the chunk.
    """
    try:
        llm = _get_llm()
        prompt = EXTRACT_QUESTIONS_PROMPT.format(text=chunk.text)
        response = llm.invoke(prompt)

        # Parse JSON from response
        content = response.content.strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        questions = json.loads(content)

        # Enrich with chunk metadata
        for q in questions:
            q["company"] = chunk.metadata.get("company", "Unknown")
            q["source_doc"] = chunk.metadata.get("source_file", "")
            q["source_page"] = chunk.metadata.get("page_number", 0)
            q["chunk_id"] = chunk.metadata.get("chunk_id", "")

        return questions

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
        return []
    except Exception as e:
        logger.error(f"Error extracting questions: {e}")
        return []


def extract_company_info(chunks: list[Document], company: str) -> dict:
    """
    Extract company metadata from the first few chunks of a company's documents.
    Uses the first chunks which typically contain overview info.
    """
    # Combine first 3 chunks for context
    combined_text = "\n\n".join(
        c.text for c in chunks[:3]
    )

    try:
        llm = _get_llm()
        prompt = EXTRACT_COMPANY_PROMPT.format(
            company=company, text=combined_text
        )
        response = llm.invoke(prompt)

        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        return json.loads(content)

    except Exception as e:
        logger.error(f"Error extracting company info for {company}: {e}")
        return {
            "company": company,
            "package": "Not mentioned",
            "role": "Not mentioned",
            "skills": [],
            "rounds": [],
            "eligibility": "Not mentioned",
        }


def extract_and_store(chunks: list[Document]) -> dict:
    """
    Extract structured data from all chunks and store in structured DB.

    Args:
        chunks: List of Document chunks (already chunked and embedded)

    Returns:
        Summary dict with counts of extracted items
    """
    if not chunks:
        return {"questions": 0, "companies": 0}

    # Group chunks by company
    company_chunks: dict[str, list[Document]] = {}
    for chunk in chunks:
        company = chunk.metadata.get("company", "Unknown")
        doc_type = chunk.metadata.get("doc_type", "")
        # Only extract from interview experiences and JDs
        if doc_type in ("interview_experience", "job_description"):
            company_chunks.setdefault(company, []).append(chunk)

    total_questions = 0
    total_companies = 0

    for company, c_chunks in company_chunks.items():
        logger.info(f"Extracting structured data for: {company} ({len(c_chunks)} chunks)")

        # Extract company info
        existing = structured_store.find_one("companies", {"company": company})
        if not existing:
            company_info = extract_company_info(c_chunks, company)
            structured_store.insert("companies", company_info)
            total_companies += 1
            logger.info(f"  Stored company info: {company}")

        # Extract questions from interview experience chunks
        ie_chunks = [c for c in c_chunks if c.metadata.get("doc_type") == "interview_experience"]
        for chunk in ie_chunks:
            questions = extract_questions_from_chunk(chunk)
            if questions:
                # Deduplicate by question text + company
                for q in questions:
                    existing_q = structured_store.find_one(
                        "interview_questions",
                        {"question": q["question"], "company": q["company"]},
                    )
                    if not existing_q:
                        structured_store.insert("interview_questions", q)
                        total_questions += 1

        logger.info(f"  Extracted {total_questions} questions for {company}")

    summary = {"questions": total_questions, "companies": total_companies}
    logger.info(f"Extraction complete: {summary}")
    return summary
