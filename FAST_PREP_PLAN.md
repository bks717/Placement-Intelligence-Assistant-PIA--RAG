# 🏗️ PIA System Architecture & RAG Blueprint

Welcome to the architectural documentation for **PIA (Placement Intelligence Assistant)**. This blueprint details the end-to-end design, data flow, and RAG pipelines for the three core capabilities of the platform:
1. **Resume & JD Analyzer (ATS Gap Assessment)**
2. **Fast Prep (Personalized Study Plan & Top Asked Questions)**
3. **About the Company (Grounded Dossier)**

---

## 🔍 Retrieval-Augmented Generation (RAG) Overview

### What is RAG?
Retrieval-Augmented Generation (RAG) is a pattern that enhances Large Language Models (LLMs) by retrieving relevant facts from an external, verified knowledge base (corpus) and inserting them into the prompt context before generating a response. This prevents hallucinations, ensures domain-specific accuracy, and allows citing sources for every claim.

### How RAG Works in PIA
In PIA, RAG is implemented using a **Hybrid Retrieval** design that merges:
1. **Dense Vector Retrieval (ChromaDB)**: Captures semantic and contextual similarity.
2. **Sparse Keyword Retrieval (BM25)**: Captures exact keyword matches (e.g., specific SQL operators, programming terms).
3. **Cross-Encoder Re-ranking**: Joint query-document validation to score and surface the top-5 most relevant chunks.

```
       [ User Query ]
             │
      ┌──────┴──────┐
      ▼             ▼
 [ChromaDB]      [BM25]
 (Dense SDE)   (Exact Match)
      │             │
      └──────┬──────┘
             ▼
      [ RRF Fusion ]
             │
             ▼
    [ Cross-Encoder ]
       Re-ranking
             │
             ▼
    [ Context Prompt ]
             │
             ▼
        [ Gemini ] ──► [ Cited Response ]
```

---

## 📄 1. Resume & JD Analyzer (ATS Gap Assessment)

### What it is
The **Resume & JD Analyzer** is an ATS-style tool that analyzes a student's resume PDF against a target Job Description (JD) PDF in-memory. It provides a match score, flags missing keywords, lists missing/preferred skills, and recommends actions to improve alignment.

### How it Works (Conceptually)
It performs a structural comparison between two unstructured texts:
1. **Resume extraction**: Analyzes sections (Work Experience, Skills, Education) and checks formatting constraints.
2. **JD extraction**: Identifies key criteria (Role, Seniority, Required Skills, Domain).
3. **Gap Analysis**: Cross-references the resume's skills/projects against the JD requirements to score compatibility.

### How it Works in the Project
1. **In-Memory Parsing**: The frontend sends the PDF bytes of both documents via a multipart request. `pdf_loader` extracts the raw text.
2. **Formatting Audit (Local)**: Zero-cost Python regular expressions run first to inspect formatting rules (e.g., presence of email, phone number, section count).
3. **LLM Extraction**: The backend sends both texts to Gemini with a highly constrained Pydantic validation schema (`ResumeAnalyzeResponse`), returning structured JSON.

### Step-by-Step Workflow Example
A student uploads `My_Resume.pdf` and `Walmart_SDE2_JD.pdf`:

1. **Input text extracted**:
   * **Resume text**: *"Bhavasmit | SDE. Skills: Java, Python, React, MySQL. Experience: Built e-commerce backend..."*
   * **JD text**: *"Walmart seeking SDE-2. Required: Java, Spring Boot, Redis, NoSQL, Kafka, 3+ years experience..."*

2. **Regex Formatting Checks (Local)**:
   * Confirms email and phone numbers are present.
   * Scans for missing sections (e.g., "Projects" is present, but "Certifications" is absent).

3. **Gemini Gap Assessment**:
   * Evaluates requirements against experience.
   * **Matched Skills**: `Java`, `React`, `MySQL`
   * **Missing Required Skills**: `Spring Boot`, `Redis`, `NoSQL`, `Kafka`

4. **Structured JSON Output**:
```json
{
  "ats_score": 68.0,
  "company": "Walmart",
  "role": "Software Engineer II",
  "matched_required_skills": ["Java", "React", "MySQL"],
  "missing_required_skills": ["Spring Boot", "Redis", "NoSQL", "Kafka"],
  "formatting_issues": ["Missing LinkedIn profile", "No mention of cloud services"],
  "priority_recommendations": [
    "Add Spring Boot and Redis experience to your technical skills section.",
    "Describe your e-commerce project backend scaling achievements using system metrics."
  ],
  "overall_verdict": "Good technical foundation, but lacks matching backend framework exposure required for SDE-2."
}
```

---

## 📅 2. Fast Prep (Day-by-Day Study Plan)

### What it is
**Fast Prep** is a structured timeline generator for SDE placement prep. If a drive is in $N$ days, it builds a day-by-day study roadmap mapping out exact **concept reference links**, **DSA practice problems**, and **most-asked company interview questions**.

### How it Works (Conceptually)
It distributes a curated curriculum across a dynamic time limit, prioritizing high-yield topics (like Arrays/Strings and basic SQL) for short timelines (e.g., 3 days) and expanding to advanced topics (like System Design and DP) for longer timelines (e.g., 30 days).

### How it Works in the Project
1. **Local RAG Retrieval**: When a student enters a company name, the pipeline queries the local `pia_chunks` database for all `doc_type="interview_experience"` and `company=company` records.
2. **Frequency Ranking**: Chunks are processed in Python using string similarity to identify and count overlapping question patterns (e.g., merging near-duplicates).
3. **Curated Banks Integration**: Rather than letting the LLM invent study materials, the system merges the retrieved questions with pre-vetted curriculum databases:
   * **Core subject bank**: Verified articles (OOPS, OS, Networks, DBMS, System Design).
   * **DSA bank**: Curated LeetCode problems (names, difficulty, and links).
4. **Deterministic Allocation**: A Python scheduling algorithm distributes the workload evenly across the days, reserving the final 1–2 days for mock practice of the top-ranked interview questions.

### Step-by-Step Workflow Example
A student requests a **5-day plan** for **ProcDNA**:

1. **Local RAG Lookup**:
   * Retrieves 15 write-up files for ProcDNA.
   * Identifies that 4 students were asked about *"SQL Joins vs Subqueries"* and 3 were asked to *"Merge Intervals"*.

2. **Workload Selection (5 Days)**:
   * Since timeline is short ($5$ days), the scheduler pulls **Easy-Medium** difficulty items.
   * Selects OOPS & SQL/DBMS buckets; skips low-priority OS/Networks buckets.
   * Selects top 5 DSA problems from the curated repository.

3. **Day-by-Day Scheduling**:
   * **Day 1**: SQL Joins & Two Sum.
   * **Day 2**: SQL Indexes & Group Anagrams.
   * **Day 3**: Polymorphism & Merge Intervals.
   * **Day 4**: System Design basics & mock interview prep.
   * **Day 5**: Solve top-asked ProcDNA questions (revising questions retrieved in Step 1).

4. **Structured JSON Output**:
```json
{
  "company": "ProcDNA",
  "days_left": 5,
  "interview_questions": [
    {
      "question": "Explain the difference between INNER JOIN and LEFT JOIN with an example",
      "asked_in": 4,
      "round": "Technical",
      "source": { "file": "ProcDNA_IE_1.pdf", "page": 3 }
    }
  ],
  "schedule": [
    {
      "day": 1,
      "focus": "SQL Joins & Arrays",
      "concepts": ["SQL Joins (INNER/LEFT/RIGHT)"],
      "dsa": ["Two Sum"],
      "revise_questions": []
    }
  ]
}
```

---

## 🏢 3. About the Company (Grounded Dossier)

### What it is
**About the Company** is a grounded intelligence report outlining a company's market overview, hiring standards, pros/cons, work-life balance, and typical SDE salaries. Every claim is backed by real, clickable web citations.

### How it Works (Conceptually)
Traditional LLMs cannot provide up-to-date details on salaries or employee reviews because their training data is static. Grounded RAG solves this by executing real-time web searches (careers pages, Glassdoor, news, annual reports) and using the search results as context to write the report.

### How it Works in the Project
1. **Live Search Integration**: The backend issues a grounded request to Gemini with Google Search enabled as a tool.
2. **Citations Extraction**: The backend parses the Gemini response metadata to extract the exact web page titles and URLs Google Search crawled.
3. **Robust Fallback Engine**: If the daily free-tier Gemini API limit is exhausted (generating a 429 error), the engine catches the exception and falls back to:
   * **Pre-generated popular dossiers** for target companies (Google, Microsoft, Amazon, Walmart, ProcDNA) to ensure zero downtime.
   * **Dynamic templates** for any other requested company names.

### Step-by-Step Workflow Example
A user searches for **Walmart**:

1. **Live Request to Gemini**:
   * System triggers Gemini with search tool enabled: *"Provide a dossier on Walmart Global Tech India salaries, pros, cons, and presence."*
   * Gemini searches Google for: `Walmart Global Tech India careers`, `Walmart salaries Glassdoor site:levels.fyi`, `Walmart India news`.

2. **Compilation**:
   * Gemini compiles the report.
   * Extracts links to the articles it referenced.

3. **Response Assembly**:
   * Merges overview, presence, pros/cons list, work-life rating, and salary ranges.
   * Attaches the source URLs so the student can verify the details.

4. **Structured JSON Output**:
```json
{
  "company": "Walmart",
  "overview": "Walmart Global Tech India builds core supply-chain and e-commerce platforms powering global retail.",
  "india_presence": "Massive offices in Bengaluru and Chennai.",
  "pros": ["Highly competitive compensation", "Tremendous engineering scale"],
  "cons": ["Bureaucracy can slow project approvals"],
  "salaries": ["Software Engineer (SDE-2): ₹18L - ₹24L per annum base"],
  "work_life_balance": "Excellent work-life balance with standard hybrid flexibility.",
  "sources": [
    { "title": "Walmart Careers Tech India", "url": "https://careers.walmart.com/global-tech-india" },
    { "title": "Glassdoor Reviews", "url": "https://www.glassdoor.com/Reviews/Walmart-Reviews-E6036.htm" }
  ]
}
```

---

## 🛠️ Summary Matrix: RAG Usage Across Features

| Feature | Where RAG is Used | Search Engine | Data Source | Citations Provided? |
|---|---|---|---|---|
| **Resume & JD Analyzer** | No RAG (Context-in-prompt) | None | Uploaded PDF bytes (In-Memory) | No |
| **Fast Prep** | Local RAG | ChromaDB + BM25 | Local `interview_experience` PDFs | Yes (File + Page number) |
| **About the Company** | Grounded Web RAG | Google Search | Live Web Index | Yes (Source Titles + URLs) |
