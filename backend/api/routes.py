"""
API Routes — FastAPI endpoints for PIA.

Endpoints:
    POST /api/query        — RAG query with company filter
    POST /api/ingest       — Trigger ingestion for uploaded PDFs
    GET  /api/companies    — List all ingested companies
    GET  /api/companies/{name} — Company details + question stats
    POST /api/resume/analyze   — Upload resume → gap analysis
    POST /api/eval/run     — Trigger evaluation harness
    GET  /api/eval/results — Get latest eval metrics
    GET  /api/stats        — System statistics
"""

import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from loguru import logger

from backend.api.schemas import (
    QueryRequest, QueryResponse,
    IngestResponse,
    CompanyInfo, CompanyListResponse,
    ResumeAnalyzeResponse,
    EvalRunRequest, EvalResultsResponse,
    StatsResponse,
)
from backend.rag.query_router import route_query
from backend.ingestion.pipeline import run_pipeline
from backend.resume.analyzer import analyze_resume
from backend.eval.run_eval import run_full_eval
from backend.db.mongo_store import structured_store
from backend.db.vector_store import vector_store
from backend.config import settings


router = APIRouter(prefix="/api", tags=["PIA API"])


# ============================================================
# Query
# ============================================================

@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    RAG query endpoint. Detects intent, routes to appropriate handler,
    returns cited answer.
    """
    logger.info(f"Query: {request.query[:80]}...")

    try:
        result = route_query(
            query=request.query,
            company=request.company,
            doc_type=request.doc_type,
        )
        return QueryResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            chunks_used=result.get("chunks_used", 0),
            intent=result.get("intent"),
            company_filter=result.get("company_filter"),
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Ingestion
# ============================================================

@router.post("/ingest", response_model=IngestResponse)
async def ingest_endpoint(
    data_dir: str = Form(default=None),
    skip_extraction: bool = Form(default=False),
    force: bool = Form(default=False),
):
    """
    Trigger PDF ingestion pipeline.
    Processes all PDFs in the data directory.
    """
    target_dir = data_dir or settings.data_dir
    logger.info(f"Ingestion triggered | dir={target_dir}")

    try:
        result = run_pipeline(
            data_dir=target_dir,
            skip_extraction=skip_extraction,
            force=force,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])

        return IngestResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/upload")
async def upload_and_ingest(
    files: list[UploadFile] = File(...),
    doc_type: str = Form(default="interview_experience"),
    company: str = Form(default="Unknown"),
    skip_extraction: bool = Form(default=False),
):
    """
    Upload PDF files and ingest them directly.
    Files are saved to the data directory, then the pipeline runs.
    """
    import shutil

    # Map doc_type to directory name
    dir_map = {
        "interview_experience": "interview_experiences",
        "job_description": "job_descriptions",
        "aptitude_material": "aptitude_material",
    }
    sub_dir = dir_map.get(doc_type, "interview_experiences")
    target_dir = Path(settings.data_dir) / sub_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue
        file_path = target_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        saved_files.append(str(file_path))
        logger.info(f"Saved uploaded file: {file_path}")

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid PDF files uploaded")

    # Run ingestion pipeline
    result = run_pipeline(
        data_dir=settings.data_dir,
        skip_extraction=skip_extraction,
    )

    return {
        "files_saved": saved_files,
        "ingestion_result": result,
    }


# ============================================================
# Companies
# ============================================================

@router.get("/companies", response_model=CompanyListResponse)
async def list_companies():
    """List all ingested companies with metadata."""
    companies_data = structured_store.find("companies")

    companies = []
    for c in companies_data:
        # Count questions for each company
        question_count = structured_store.count(
            "interview_questions",
            {"company": c.get("company", "")},
        )
        companies.append(CompanyInfo(
            company=c.get("company", "Unknown"),
            package=c.get("package", "Not mentioned"),
            role=c.get("role", "Not mentioned"),
            skills=c.get("skills", []),
            rounds=c.get("rounds", []),
            eligibility=c.get("eligibility", "Not mentioned"),
            total_questions=question_count,
        ))

    # Also check for companies from ingested files that might not be in structured store
    ingested = structured_store.find("ingested_files")
    known_companies = {c.company for c in companies}
    for f in ingested:
        name = f.get("file_name", "").replace(".pdf", "").replace("_JD", "").replace("_", " ")
        # Simple extraction — just use the file name
        for prefix in ["Interview Experience ", "IE "]:
            if name.startswith(prefix):
                name = name[len(prefix):]
        if name and name not in known_companies:
            companies.append(CompanyInfo(company=name))
            known_companies.add(name)

    return CompanyListResponse(
        companies=companies,
        total=len(companies),
    )


@router.get("/companies/{name}")
async def get_company_detail(name: str):
    """Get detailed company info including questions and topic distribution."""
    company_info = structured_store.find_one("companies", {"company": name})
    questions = structured_store.find("interview_questions", {"company": name})

    # Topic distribution
    topic_counts = {}
    for q in questions:
        topic = q.get("topic", "General")
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    # Difficulty distribution
    diff_counts = {}
    for q in questions:
        diff = q.get("difficulty", "Unknown")
        diff_counts[diff] = diff_counts.get(diff, 0) + 1

    return {
        "company": company_info or {"company": name},
        "questions": questions,
        "total_questions": len(questions),
        "topic_distribution": topic_counts,
        "difficulty_distribution": diff_counts,
    }


# ============================================================
# Resume Analyzer
# ============================================================

@router.post("/resume/analyze", response_model=ResumeAnalyzeResponse)
async def analyze_resume_endpoint(
    company: str = Form(...),
    resume_file: UploadFile = File(None),
    resume_text: str = Form(default=""),
):
    """
    Analyze a resume against a company's JD.
    Upload a PDF or provide text directly.
    Resume content is processed in-memory only — never persisted.
    """
    text = resume_text
    pdf_bytes = None

    if resume_file and resume_file.filename:
        if not resume_file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        pdf_bytes = await resume_file.read()

    if not text and not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="Provide either resume_text or upload a resume_file",
        )

    try:
        result = analyze_resume(
            resume_text=text,
            company=company,
            resume_pdf_bytes=pdf_bytes,
        )

        if "error" in result and not result.get("match_score"):
            raise HTTPException(status_code=400, detail=result["error"])

        return ResumeAnalyzeResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Evaluation
# ============================================================

@router.post("/eval/run")
async def run_eval_endpoint(request: EvalRunRequest):
    """Trigger the evaluation harness."""
    try:
        results = run_full_eval(
            modes=request.modes,
            include_faithfulness=request.include_faithfulness,
        )
        return results
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/eval/results")
async def get_eval_results():
    """Get the latest evaluation results."""
    results_path = Path(__file__).parent.parent / "eval" / "eval_results.json"
    if not results_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No evaluation results found. Run POST /api/eval/run first.",
        )

    with open(results_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# System Stats
# ============================================================

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics."""
    try:
        vs_stats = vector_store.get_stats()
    except Exception:
        vs_stats = {"total_chunks": 0}

    ss_stats = structured_store.get_stats()
    ingested_count = structured_store.count("ingested_files")

    return StatsResponse(
        vector_store_chunks=vs_stats.get("total_chunks", 0),
        structured_store=ss_stats,
        ingested_files=ingested_count,
    )
