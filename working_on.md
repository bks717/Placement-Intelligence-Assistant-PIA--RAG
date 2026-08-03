# 📝 Project Progress & Handoff Document (working_on.md)

This document keeps track of recent architectural decisions, changes, and the current deployment state of the **Placement Buddy Puddy (Puddy)** project. Use this as a reference context for future development sessions or handover to other AI assistants.

---

## 🚀 Recent Major Accomplishments

### 1. Split-Cloud Deployment Architecture
* **Frontend (React/Vite)**: Deployed on **Vercel** as a high-performance static build.
  * *Reasoning:* Static builds on Vercel are fast, robust, and free of cold-starts.
  * *File modified:* [vercel.json](file:///c:/Users/bhava/OneDrive/Desktop/RAG_PROJECT/vercel.json) (restricted to static-build targets, removed Python builders).
* **Backend (FastAPI)**: Deployed on **Render** as a Python web service.
  * *Reasoning:* Bypasses Vercel's Serverless Function size limit (250MB) and file-locking constraints on database folders (e.g., ChromaDB).
  * *File created:* [render.yaml](file:///c:/Users/bhava/OneDrive/Desktop/RAG_PROJECT/render.yaml) (Render Blueprint configuration for one-click deployment).

### 2. Groq Provider Integration (`groq integ`)
* Added **Groq** as the primary provider for non-grounded LLM completions (like Resume ATS parsing, database query intent routing, and structured entity extraction).
* Implemented a fallback chain inside [llm_client.py](file:///c:/Users/bhava/OneDrive/Desktop/RAG_PROJECT/backend/rag/llm_client.py):
  1. Primary: **Groq** (`ChatGroq` model via `openai/gpt-oss-20b` or custom key configuration).
  2. Fallback: **Gemini (lite)** when Groq is rate-limited or unconfigured.
  * *Reasoning:* Groq has a separate, generous free tier which helps save Gemini API quotas. Gemini remains the primary provider for grounded research (since it uses Google Search).

### 3. Anti-Quota Exhaustion (429) Fallback System
* Implemented a robust fallback system in [company_report.py](file:///c:/Users/bhava/OneDrive/Desktop/RAG_PROJECT/backend/rag/company_report.py) and [interview_questions.py](file:///c:/Users/bhava/OneDrive/Desktop/RAG_PROJECT/backend/rag/interview_questions.py):
  * On Gemini `429 RESOURCE_EXHAUSTED` (daily limit reached), the system catches the error.
  * It returns **high-quality, pre-generated dossiers/questions** for popular target companies: **Google, Walmart, Amazon, Microsoft, and ProcDNA**.
  * For other companies, it compiles a dynamic template report instead of failing with a raw error.

---

## 🛠️ Current Project State & Config

### 1. Database Connectors
* Supports **MongoDB Atlas** (using pymongo) and falls back to **JSONStore** (local file-based storage).
* Whitelist IP restrictions on MongoDB Atlas can trigger TLS errors; in such cases, setting `USE_MONGODB=false` routes data to `/tmp/json_data` gracefully without crashing backend startup.

### 2. Server API Link
* The frontend reads `import.meta.env.VITE_API_BASE_URL` to route requests. If unset (local dev), it defaults to `/api` proxying requests to `localhost:8000`.

---

## 🚀 Current Deployment Status (Completed)

* **Backend Service**:
  * **Status**: **Live & Healthy**
  * **Platform**: Render
  * **Endpoint**: `https://placement-intelligence-assistant-pia-rag.onrender.com`
  * **Database**: MongoDB Atlas Cluster connected and whitelisted.
  * **LLM Engine**: Groq (primary) + Gemini (fallback) fully integrated.

* **Frontend UI**:
  * **Status**: **Live & Fully Connected**
  * **Platform**: Vercel
  * **API URL Env Configured**: `VITE_API_BASE_URL = https://placement-intelligence-assistant-pia-rag.onrender.com/api` (re-compiled static client).
  * **CORS Settings**: Fully configured on Render backend to permit requests from the Vercel app domain.
