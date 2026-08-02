"""
Top Asked — web-grounded DSA + core-subject interview questions for a company.

"Top Asked" tab of Fast Prep. Uses Gemini with Google Search grounding (the same
approach as company_report.py) so every question is backed by a REAL web source:
GeeksforGeeks, LeetCode Discuss, Glassdoor, AmbitionBox, InterviewBit, blogs,
company experience pages. Source titles + URLs come straight from
grounding_metadata.

SDE/software-role oriented by design: only technical questions. DSA questions and
core-subject conceptual questions (OOPS/DBMS/SQL/OS/CN/System Design) are
separated into two lists. HR / behavioural / "tell me about yourself" questions
are excluded.

Why web grounding and not the ChromaDB corpus? The ingested corpus is tiny and
sparse — most companies have no interview-experience PDFs. For "what all does
this company actually ask", live web retrieval is the only source with real
coverage.

Model note: grounding needs a FULL model (lite = instant 429 on free tier);
thinking_budget=512 keeps it at ~10-24s while still producing grounding sources.
"""

import json
import time
from typing import Optional
from loguru import logger

from backend.config import settings


# ─────────────────────────────────────────────
# Prompt — structured JSON, grounded, no markdown
# ─────────────────────────────────────────────

PROMPT = """\
You are a placement-prep research analyst for an INDIAN engineering student preparing for an SDE (software development engineer) role at "{company}". Use the web search tool (never rely on memory) to research what questions this company ACTUALLY asks in its technical interviews, then produce a structured list.

Focus: what the company asks in SOFTWARE / SDE / ENGINEERING interviews (campus + experienced). Search sites like GeeksforGeeks, LeetCode Discuss, Glassdoor, AmbitionBox, InterviewBit, CareerCup, and personal experience blogs.

Return ONLY raw JSON (no markdown fences, no explanation) in exactly this shape:
{{
  "role": "the SDE/software role these questions apply to, from the sources (e.g. 'Software Development Engineer', 'Software Engineer')",
  "dsa_questions": [
    {{"question": "the coding/DSA question, one clear line", "difficulty": "Easy|Medium|Hard", "topic": "e.g. Arrays, Strings, Trees, DP"}}
  ],
  "core_questions": [
    {{"question": "the conceptual question, one clear line", "subject": "OOPS|DBMS|SQL|Operating Systems|Computer Networks|System Design"}}
  ],
  "sources": [
    {{"title": "page title", "url": "https://..."}}
  ]
}}

GROUNDING RULES
- Every question MUST be one this company actually asks, per the sources you found. Do NOT invent questions. Do NOT pad with generic questions the company isn't known for.
- dsa_questions: coding/algorithm questions. Include the difficulty and a topic tag.
- core_questions: conceptual questions about OOPS, DBMS, SQL, Operating Systems, Computer Networks, or System Design. Use EXACTLY one of those six subject labels in "subject".
- STRICTLY EXCLUDE: HR, behavioural, situational, managerial, and resume-based questions ("Tell me about yourself", "Where do you see yourself in 5 years?", salary expectations, etc.). TECHNICAL / SDE questions ONLY.
- Aim for 8-15 questions in EACH of dsa_questions and core_questions.
- Sources MUST be the actual URLs returned by the search tool — do not invent or reconstruct URLs.
- Every question must be supported by a source in "sources".
- If you cannot find reliable technical-interview information for this company, return:
  {{"error": "No reliable technical-interview information found for this company."}}
"""


# ─────────────────────────────────────────────
# Main public function
# ─────────────────────────────────────────────

def fetch_interview_questions(company: str, role: str = "") -> dict:
    """
    Web-grounded DSA + core-subject interview questions for a company.

    Returns {company, role, dsa_questions, core_questions, sources, note} — or
    {"error": ...}.
    """
    t0 = time.time()
    company = (company or "").strip()
    role = (role or "").strip()

    if not company:
        return {"error": "Enter a company name first."}

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.google_api_key)

        prompt = PROMPT.format(company=company)
        if role:
            prompt += f'\n\n(For context, the plan targets the role "{role}" — keep questions relevant to it.)'

        resp = client.models.generate_content(
            model=settings.llm_grounding_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.0,
            ),
        )

        # Grounding metadata → real web sources (title + url)
        sources = []
        try:
            gm = resp.candidates[0].grounding_metadata
            for chunk in (gm.grounding_chunks or []):
                web = getattr(chunk, "web", None)
                if web is not None and getattr(web, "uri", None):
                    title = getattr(web, "title", None) or web.uri
                    if not any(s["url"] == web.uri for s in sources):
                        sources.append({"title": title, "url": web.uri})
        except Exception as e:
            logger.warning(f"Could not extract grounding sources: {e}")

        text = (resp.text or "").strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0].strip()

        data = json.loads(text)

    except json.JSONDecodeError as e:
        logger.error(f"Top Asked JSON parse failed: {e}\nRaw: {text[:300]}")
        return {"error": "The research service returned malformed data. Please try again."}
    except Exception as e:
        msg = str(e)
        logger.error(f"Top Asked failed: {msg}")
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
            return {"error": "The AI service is rate-limited right now (free-tier quota). Please wait about a minute and try again."}
        return {"error": "Could not research that company. Please try again in a moment."}

    logger.info(f"Top Asked for '{company}' done in {time.time()-t0:.1f}s ({len(sources)} sources)")

    # If the model says it found nothing, honour that
    if data.get("error"):
        return {"error": data["error"]}

    # ── Defensive normalization ──
    def _lst(key):
        v = data.get(key)
        return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []

    # DSA questions — drop rows without a question, normalize difficulty
    _DIFFS = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}
    dsa_questions = []
    for item in _lst("dsa_questions"):
        q = (item.get("question") or "").strip()
        if not q:
            continue
        diff = str(item.get("difficulty") or "").strip().lower()
        dsa_questions.append({
            "question": q,
            "difficulty": _DIFFS.get(diff, "Medium"),
            "topic": (item.get("topic") or "").strip(),
        })

    # Core questions — drop rows without a question, normalize subject to the
    # six canonical labels (map common variants like OS/CN/Networks).
    canon = {
        "oops": "OOPS", "oop": "OOPS", "object oriented": "OOPS",
        "dbms": "DBMS", "database": "DBMS",
        "sql": "SQL", "mysql": "SQL", "databases": "DBMS",
        "os": "Operating Systems", "operating systems": "Operating Systems", "operating system": "Operating Systems",
        "cn": "Computer Networks", "computer networks": "Computer Networks", "networks": "Computer Networks",
        "system design": "System Design", "sd": "System Design", "system-design": "System Design",
    }
    core_questions = []
    for item in _lst("core_questions"):
        q = (item.get("question") or "").strip()
        if not q:
            continue
        subj = canon.get(str(item.get("subject") or "").strip().lower(), "Core")
        core_questions.append({"question": q, "subject": subj})

    # Merge model sources + grounding sources, de-dupe by URL (grounding is
    # authoritative — the model may invent titles for real grounding URLs)
    merged = list(sources)
    model_sources = data.get("sources")
    if isinstance(model_sources, list):
        for s in model_sources:
            if not isinstance(s, dict):
                continue
            url = s.get("url")
            title = s.get("title")
            if url and not any(ex["url"] == url for ex in merged):
                merged.append({"title": title or url, "url": url})

    # If nothing usable came back, say so honestly rather than fabricate
    if not dsa_questions and not core_questions:
        return {"error": "No technical-interview questions found for this company."}

    note = ""
    if role:
        note = f"Focused on {role} interviews."

    return {
        "company": company,
        "role": (data.get("role") or "").strip() or role or "",
        "dsa_questions": dsa_questions,
        "core_questions": core_questions,
        "sources": merged,
        "note": note,
    }
