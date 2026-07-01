# PIA — Placement Intelligence Assistant

An AI-powered placement preparation platform built on a production-style **hybrid RAG pipeline** (BM25 + dense retrieval + cross-encoder re-ranking + source citations + evaluation harness).

## Features

### MVP (Fully Built)
- **Ingestion Pipeline**: PDF loader → doc-type-aware chunker → sentence-transformer embeddings → ChromaDB + structured store
- **Hybrid Retrieval**: BM25 (keyword) + dense vector search with Reciprocal Rank Fusion (RRF)
- **Cross-Encoder Re-ranking**: ms-marco-MiniLM re-scores top-20 → returns top-5 most relevant
- **Source-Cited Q&A**: Every answer cites source file and page number; anti-hallucination guardrails
- **Resume Analyzer**: Resume vs JD skill match + gap list + recommendations (PII-safe)
- **Evaluation Harness**: 30 labeled Q&A pairs, precision@k / recall@k / MRR, before/after comparison
- **Smart Query Router**: Intent detection routes between RAG, structured queries, and multi-company comparison

### Stretch (Designed)
- Preparation Roadmap Generator
- Interview Pattern Mining + dashboards
- AI Mock Interview with rubric-based grading

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI, LangChain, Python 3.11+ |
| LLM | Google Gemini (gemini-2.5-flash) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Re-ranker | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| Vector DB | ChromaDB |
| Structured Store | JSON (MongoDB-ready interface) |
| Frontend | React + Vite + Vanilla CSS |
| Evaluation | Custom harness + RAGAS-compatible |

## Quick Start

### 1. Clone & Setup

```bash
cd RAG_PROJECT

# Copy env file and add your Gemini API key
cp .env.example .env
# Edit .env → set GOOGLE_API_KEY
```

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Create Sample Data

```bash
python -m backend.scripts.create_sample_data
```

### 4. Run Ingestion Pipeline

```bash
# Basic ingestion (no LLM extraction — doesn't need API key)
python -m backend.ingestion.pipeline --data-dir ./data --skip-extraction

# Full ingestion (with structured extraction — needs API key)
python -m backend.ingestion.pipeline --data-dir ./data
```

### 5. Start Backend

```bash
python -m backend.main
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 6. Start Frontend

```bash
cd frontend
npm install
npm run dev
# UI available at http://localhost:5173
```

### 7. Run Evaluation

```bash
# Retrieval metrics only
python -m backend.eval.run_eval

# With faithfulness scoring (requires API key)
python -m backend.eval.run_eval --faithfulness
```

## Architecture

```
User Query → Embedding → Metadata Filter (company=X)
                |
                ▼
    Hybrid Retrieval (BM25 + dense) → top 20
                |
                ▼
          Re-ranker → top 5
                |
                ▼
     LLM (Gemini) + cited chunks
                |
                ▼
    Answer with source + page citation
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/query` | RAG query with company filter |
| `POST` | `/api/ingest` | Trigger ingestion pipeline |
| `POST` | `/api/ingest/upload` | Upload + ingest PDFs |
| `GET` | `/api/companies` | List all companies |
| `GET` | `/api/companies/{name}` | Company details + questions |
| `POST` | `/api/resume/analyze` | Resume gap analysis |
| `POST` | `/api/eval/run` | Run evaluation harness |
| `GET` | `/api/eval/results` | Get eval metrics |
| `GET` | `/api/stats` | System statistics |

## Project Structure

```
RAG_PROJECT/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py             # Pydantic settings
│   ├── ingestion/            # PDF → chunks → embeddings
│   ├── rag/                  # Hybrid retrieval + reranking + generation
│   ├── eval/                 # Evaluation harness
│   ├── resume/               # Resume analyzer
│   ├── api/                  # FastAPI routes + schemas
│   ├── db/                   # ChromaDB + structured store wrappers
│   └── scripts/              # Data generation utilities
├── frontend/                 # React + Vite
│   └── src/
│       ├── components/       # Sidebar
│       ├── pages/            # Dashboard, Query, Companies, Resume, Eval, Admin
│       └── services/         # API client
├── data/                     # PDF documents (gitignored)
├── .env.example
├── docker-compose.yml
└── README.md
```

## Key Design Decisions

1. **Metadata filtering BEFORE retrieval** — cuts search space, doesn't post-filter
2. **BM25 + Dense hybrid** — BM25 catches exact SQL keywords; dense captures semantic paraphrases
3. **RRF fusion** — industry-standard score normalization between heterogeneous rankers
4. **Cross-encoder re-ranking** — bi-encoders miss subtle relevance; cross-encoder does full attention
5. **Dual storage** — vector DB for semantic search, structured store for aggregation queries
6. **PII handling** — resume text never persisted; processed in-memory only
7. **Evaluation harness** — quantitative proof with before/after numbers, not just "I added a reranker"
