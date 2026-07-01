"""
API Schemas — Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ============================================================
# Query Endpoints
# ============================================================

class QueryRequest(BaseModel):
    """Request body for the /api/query endpoint."""
    query: str = Field(..., min_length=1, max_length=2000, description="The user's question")
    company: Optional[str] = Field(None, description="Filter to specific company")
    doc_type: Optional[str] = Field(None, description="Filter to doc type: interview_experience, job_description, aptitude_material")

    model_config = {"json_schema_extra": {
        "examples": [
            {"query": "What SQL questions were asked in ProcDNA?", "company": "ProcDNA"},
            {"query": "Compare ProcDNA and Walmart interview difficulty"},
        ]
    }}


class SourceCitation(BaseModel):
    """A source citation for a retrieved chunk."""
    file: str
    page: int | str
    company: str
    doc_type: str
    chunk_preview: str
    rerank_score: Optional[float] = None


class QueryResponse(BaseModel):
    """Response from the /api/query endpoint."""
    answer: str
    sources: list[SourceCitation]
    chunks_used: int
    intent: Optional[str] = None
    company_filter: Optional[str] = None


# ============================================================
# Ingestion Endpoints
# ============================================================

class IngestResponse(BaseModel):
    """Response from the /api/ingest endpoint."""
    files_processed: int
    pages_loaded: int
    chunks_created: int
    chunks_stored: int
    questions_extracted: int = 0
    companies_extracted: int = 0


# ============================================================
# Company Endpoints
# ============================================================

class CompanyInfo(BaseModel):
    """Company information from structured store."""
    company: str
    package: str = "Not mentioned"
    role: str = "Not mentioned"
    skills: list[str] = []
    rounds: list[str] = []
    eligibility: str = "Not mentioned"
    total_questions: int = 0


class CompanyListResponse(BaseModel):
    """Response from /api/companies listing."""
    companies: list[CompanyInfo]
    total: int


# ============================================================
# Resume Analyzer
# ============================================================

class ResumeAnalyzeRequest(BaseModel):
    """Request body for resume analysis (when sending text directly)."""
    company: str = Field(..., description="Target company to compare against")
    resume_text: Optional[str] = Field(None, description="Resume text (alternative to file upload)")


class ResumeAnalyzeResponse(BaseModel):
    """Response from resume analysis."""
    company: str
    role: str
    match_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    extra_skills: list[str]
    resume_skills_count: int
    jd_skills_count: int
    recommendations: list[str]
    error: Optional[str] = None


# ============================================================
# Evaluation
# ============================================================

class EvalRunRequest(BaseModel):
    """Request to trigger evaluation."""
    modes: list[str] = Field(
        default=["dense_only", "hybrid", "hybrid_reranked"],
        description="Retrieval modes to evaluate",
    )
    include_faithfulness: bool = Field(
        default=False,
        description="Include LLM-as-judge faithfulness scoring",
    )


class EvalMetrics(BaseModel):
    """Aggregated evaluation metrics."""
    avg_precision_at_5: Optional[float] = Field(None, alias="avg_precision@5")
    avg_recall_at_5: Optional[float] = Field(None, alias="avg_recall@5")
    avg_mrr: Optional[float] = None
    avg_retrieval_time_ms: Optional[float] = None
    avg_faithfulness_score: Optional[float] = None

    model_config = {"populate_by_name": True}


class EvalResultsResponse(BaseModel):
    """Response with evaluation results."""
    timestamp: str
    eval_set_size: int
    modes: dict


# ============================================================
# General
# ============================================================

class StatsResponse(BaseModel):
    """System statistics."""
    vector_store_chunks: int
    structured_store: dict
    ingested_files: int
