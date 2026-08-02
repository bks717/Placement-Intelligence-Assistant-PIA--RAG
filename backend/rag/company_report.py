"""
Company Report — Google-Search-grounded overview (India-first).

"About the Company" feature. Uses Gemini with Google Search grounding so every
claim (pros, cons, salaries, work-life balance) is backed by real web
sources: company profile, annual reports, careers page, employee reviews, salary
reports, recent news. Source titles + URLs come straight from grounding_metadata.

INDIA-FIRST by design: the reader is an Indian student who will interview and be
placed in India, so the report prioritizes the company's India operations, Indian
employee reviews, India news, and salary figures in INR (₹). Global vs India
experiences often differ — both are surfaced when they diverge.

Why not the ChromaDB RAG pipeline? The ingested corpus only contains
interview-experience/JD PDFs — no employee reviews, salary reports or news.
Grounding IS RAG (live web retrieval + generation), just with a bigger corpus.

Model note: grounding needs a FULL model (lite = instant 429 on free tier);
thinking_budget=512 keeps it at ~10-24s instead of ~32s uncapped.
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
You are a placement-prep research analyst for an INDIAN student preparing for campus placement. Research the company "{company}" using the web search tool (never rely on memory) and produce a structured dossier.

INDIA FIRST — this report is read by a student who will interview and work in INDIA:
- If the company is global, PRIORITIZE its India operations: India offices/cities, hiring scale in India, the experience of Indian employees, and India-specific news.
- Prefer India-focused sources when they exist: AmbitionBox, Glassdoor India, Indeed India, Indian business press, and the company's India careers page.
- A company can be great abroad but weaker in India (or the reverse). When the two differ, present the INDIA experience first and note the difference.
- ALL salary figures MUST be in Indian Rupees (₹), e.g. "₹8-12 LPA". If a source reports a foreign currency, convert it to approximate INR (~₹85-90 per USD, or a reasonable current rate for other currencies), label it "approx", and keep the source.
- Recent news: prioritize India news (hiring drives, campus programs, expansion, India pay/benefit changes) over global news.

Include ALL of these source types where they exist:
- Company profile / about page (India site preferred)
- Annual reports (India-relevant figures)
- Careers page (India hiring)
- Employee reviews (AmbitionBox, Glassdoor India, Indeed India, etc.)
- Salary reports (India data)
- Recent news (India-focused, last 6-12 months)

Return ONLY raw JSON (no markdown fences, no explanation) in exactly this shape:
{{
  "overview": "2-4 sentence factual overview: what the company does, scale, notable facts — with its India footprint called out.",
  "india_presence": "2-3 sentences on India operations: offices/cities, approximate India headcount, whether they hire freshers, and campus program name if any.",
  "pros": ["4-6 genuine positives from INDIAN employee reviews, each a complete sentence"],
  "cons": ["4-6 genuine negatives from INDIAN employee reviews, each a complete sentence"],
  "salaries": ["3-5 salary data points for INDIA roles in INR, e.g. 'Fresher Software Engineer: ₹4-7 LPA (AmbitionBox)'. Use ranges, not a single figure"],
  "work_life_balance": "2-4 sentences on work culture, hours, and WLB in INDIA from Indian reviews — balanced, name both good and bad.",
  "sources": [
    {{"title": "page title", "url": "https://..."}}
  ]
}}

Grounding rules:
- Every claim in pros/cons/salaries/work_life_balance MUST be supported by a source in "sources".
- Sources MUST be the actual URLs returned by the search tool — do not invent or reconstruct URLs.
- If the company has no meaningful India presence or no public data, return:
  {{"error": "No reliable public information found about this company's India presence."}}
"""


# ─────────────────────────────────────────────
# Main public function
# ─────────────────────────────────────────────

def generate_company_report(company: str) -> dict:
    """
    India-first grounded company dossier via Gemini + Google Search.

    Returns {company, overview, india_presence, pros, cons, salaries,
             work_life_balance, sources} — or {"error": ...}.
    """
    t0 = time.time()
    company = (company or "").strip()

    if not company:
        return {"error": "Enter a company name first."}

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.google_api_key)

        resp = client.models.generate_content(
            model=settings.llm_grounding_model,
            contents=PROMPT.format(company=company),
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
        logger.error(f"Company report JSON parse failed: {e}\nRaw: {text[:300]}")
        return {"error": "The research service returned malformed data. Please try again."}
    except Exception as e:
        msg = str(e)
        logger.error(f"Company report failed: {msg}")
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
            return {"error": "The AI service is rate-limited right now (free-tier quota). Please wait about a minute and try again."}
        return {"error": "Could not research that company. Please try again in a moment."}

    logger.info(f"Company report for '{company}' done in {time.time()-t0:.1f}s ({len(sources)} sources)")

    # If the model says it found nothing, honour that
    if data.get("error"):
        return {"error": data["error"]}

    # Defensive normalization — the LLM occasionally returns wrong types
    def _lst(key):
        v = data.get(key)
        return [str(x) for x in v] if isinstance(v, list) else []

    def _str(key, default=""):
        v = data.get(key)
        return str(v) if v not in (None, "") else default

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

    return {
        "company": company,
        "overview": _str("overview", "No overview available."),
        "india_presence": _str("india_presence"),
        "pros": _lst("pros"),
        "cons": _lst("cons"),
        "salaries": _lst("salaries"),
        "work_life_balance": _str("work_life_balance", "No work-life balance data available."),
        "sources": merged,
    }
