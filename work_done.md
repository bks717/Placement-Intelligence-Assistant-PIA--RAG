# 📝 Project Progress & Work Done (work_done.md)

This document keeps track of architectural decisions, completed stages, and the history of changes made to the **Placement Buddy Puddy (Puddy)** project.

---

## 🚀 Recent Completed Stages & Commits

Here is the log of completed tasks in this session, divided by stage and tracked by their git commits:

### Stage 1: Production 422 Errors & Grounding Configuration
* **Commit**: `43d5191` — *fix: make jd_file optional in fast-prep route to avoid 422, and remove incompatible thinking_config from grounding calls*
  * **Details**: 
    * Updated the backend `/fast-prep/plan` route parameters to use standard `jd_file: Optional[UploadFile] = None` instead of `File(default=None)`. This prevents FastAPI from throwing a validation error (422) when the client omits the optional JD PDF file field from the form boundary payload.
    * Removed the reasoning `thinking_config` parameters from Google Search grounding calls in `company_report.py` and `interview_questions.py`. Reasoning budgets are unsupported on standard flash models like `gemini-2.5-flash` or `gemini-3.1-flash-lite`, which previously caused grounding failures.

### Stage 2: 100% MongoDB Atlas Vector Search Migration
* **Commit**: `f156370` — *feat: migrate vector database from ChromaDB to MongoDB Atlas Vector Search*
  * **Details**: 
    * Consolidated the database tier by migrating from the local, file-based **ChromaDB** database to **MongoDB Atlas Vector Search**. This resolves file-locking and ephemeral disk-wipe bugs on Render containers.
    * Rewrote `vector_store.py` to insert chunks with `UpdateOne` bulk queries, perform semantic similarity lookup using the Atlas `$vectorSearch` aggregation pipeline, and dynamically map query filters.
    * Removed the heavy `chromadb` dependency from root and backend `requirements.txt` files, making builds faster.
* **Commit**: `4aaf8ae` — *fix: resolve Optional NameError and Pydantic validation error for extra env inputs*
  * **Details**:
    * Fixed a `NameError` in `routes.py` by replacing `Optional` type hints with modern Python 3.10 native type unions (`UploadFile | None`).
    * Configured Pydantic Settings class with `extra = "ignore"` to ignore leftover legacy environment parameters (like `CHROMA_PERSIST_DIR`) instead of throwing validation startup crashes. Cleaned up the unused `chroma_path` property.

### Stage 3: Fast Prep Planner Input "OR" Condition
* **Commit**: `892d3a9` — *fix: make fast prep plan work with only company name or only JD*
  * **Details**:
    * Updated the Fast Prep planner prompt and validation logic in `fast_prep.py` to support building a day-by-day study schedule if *either* the company name or a JD PDF is provided.
    * If only a company is entered and no experiences exist in the database, the LLM will utilize generalized knowledge of that company's SDE interviews rather than failing with a "Not enough data" error.

### Stage 4: Responsive Mobile Layout & Navigation Drawer
* **Commit**: `770fff0` — *style: add responsive mobile top header and toggle drawer state for sidebar*
  * **Details**:
    * Resolved mobile layout overlap issues by adding a frosted top header bar (`.mobile-header`) containing a hamburger menu button and a backdrop overlay (`.sidebar-overlay`) to `App.jsx`, `Sidebar.jsx`, and `index.css`.
    * Configured the drawer menu to slide out on screens <= `1024px` and dismiss automatically when selecting sidebar links or tapping the background backdrop.

### Stage 5: Single-Page Application (SPA) Fallback Routing
* **Commit**: `937fc32` — *fix: configure vercel.json to support React Router fallback routing and api proxy redirects*
  * **Details**:
    * Modified `vercel.json` to handle client-side routing fallback rewrites to `/index.html`, resolving 404 errors when users refresh virtual routes or access pages directly (e.g. `/companies`).
    * Added reverse-proxy mapping rules for `/api` requests to route directly to the Render backend server.

---

## 🚀 Historical Accomplishments

### 1. Split-Cloud Deployment Architecture
* **Frontend (React/Vite)**: Deployed on **Vercel** as a high-performance static build.
  * *Reasoning:* Static builds on Vercel are fast, robust, and free of cold-starts.
  * *File modified:* `vercel.json` (restricted to static-build targets, removed Python builders).
* **Backend (FastAPI)**: Deployed on **Render** as a Python web service.
  * *Reasoning:* Bypasses Vercel's Serverless Function size limit (250MB) and file-locking constraints on database folders (e.g., ChromaDB).
  * *File created:* `render.yaml` (Render Blueprint configuration for one-click deployment).

### 2. Groq Provider Integration (`groq integ`)
* Added **Groq** as the primary provider for non-grounded LLM completions (like Resume ATS parsing, database query intent routing, and structured entity extraction).
* Implemented a fallback chain inside `llm_client.py`:
  1. Primary: **Groq** (`ChatGroq` model via `openai/gpt-oss-20b` or custom key configuration).
  2. Fallback: **Gemini (lite)** when Groq is rate-limited or unconfigured.
  * *Reasoning:* Groq has a separate, generous free tier which helps save Gemini API quotas. Gemini remains the primary provider for grounded research (since it uses Google Search).

### 3. Anti-Quota Exhaustion (429) Fallback System
* Implemented a robust fallback system in `company_report.py` and `interview_questions.py`:
  * On Gemini `429 RESOURCE_EXHAUSTED` (daily limit reached), the system catches the error.
  * It returns **high-quality, pre-generated dossiers/questions** for popular target companies: **Google, Walmart, Amazon, Microsoft, and ProcDNA**.
  * For other companies, it compiles a dynamic template report instead of failing with a raw error.

---

## 🛠️ Current Project State & Config

### 1. Database Connectors
* Consolidates both structured metadata and vector search into a single remote **MongoDB Atlas** cluster.
* Uses the `$vectorSearch` pipeline stage and a custom Atlas Search Index to query document embeddings.

### 2. Server API Link
* Configured Vercel rewrites to proxy `/api` routes directly to the Render backend server URL.

---

## 🚀 Current Deployment Status (Live)

* **Backend Service**:
  * **Status**: **Live & Healthy**
  * **Platform**: Render
  * **Endpoint**: `https://placement-intelligence-assistant-pia-rag.onrender.com`
  * **Database**: MongoDB Atlas Cluster connected.
  * **LLM Engine**: Groq (primary) + Gemini (fallback) fully integrated.

* **Frontend UI**:
  * **Status**: **Live & Fully Connected**
  * **Platform**: Vercel
  * **Domain**: `https://puddy.krupakara.space`
  * **CORS Settings**: Fully configured on Render backend to permit requests from the Vercel app domain.
