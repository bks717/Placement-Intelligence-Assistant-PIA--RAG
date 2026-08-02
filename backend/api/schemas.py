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


class CompanyAboutRequest(BaseModel):
    """Request body for the grounded 'About the Company' report."""
    company: str = Field(..., min_length=1, max_length=120, description="Company name to research")


class CompanySource(BaseModel):
    """A real web source backing the report."""
    title: str
    url: str


class CompanyAboutResponse(BaseModel):
    """
    Grounded company dossier — every claim backed by real web sources
    (company profile, annual reports, careers page, reviews, salary reports, news).
    """
    company: str
    overview: str
    pros: list[str] = []
    cons: list[str] = []
    salaries: list[str] = []
    work_life_balance: str
    sources: list[CompanySource] = []


# ============================================================
# Resume Analyzer
# ============================================================

class ATSSectionScores(BaseModel):
    """Per-category ATS scores, each 0-100."""
    skills_match: float
    keyword_density: float
    section_completeness: float
    experience_alignment: float
    education_match: float
    formatting: float


class ResumeAnalyzeResponse(BaseModel):
    """
    Response from ATS-style resume analysis.
    Both PDFs are analyzed in-memory — nothing is persisted.
    """
    # JD details extracted from the uploaded JD PDF
    company: str
    role: str
    seniority_level: str
    industry_domain: str
    required_experience_years: Optional[int] = None
    required_degree: Optional[str] = None

    # Overall ATS score
    ats_score: float

    # Per-section breakdown
    section_scores: ATSSectionScores

    # Skills
    matched_required_skills: list[str]
    missing_required_skills: list[str]
    matched_preferred_skills: list[str]
    missing_preferred_skills: list[str]

    # Keywords
    matched_keywords: list[str]
    missing_keywords: list[str]

    # Experience & Education detected in resume
    experience_years_detected: Optional[int] = None
    education_detected: Optional[str] = None

    # Formatting
    formatting_issues: list[str]
    formatting_positives: list[str]

    # Recommendations & verdict
    priority_recommendations: list[str]
    strengths: list[str]
    overall_verdict: str

    # Summary counts
    total_required_skills: int
    total_keywords: int

    # Error (only set on failure)
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
