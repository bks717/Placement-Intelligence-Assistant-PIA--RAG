# Fast Prep — Implementation Plan v2 (DRAFT)

> This is a **plan document only** — nothing has been implemented yet.
> v2 changes: aptitude removed · company interview questions promoted to an
> always-on compartment · exact DSA problems + exact concepts + links specified.

---

## 1. What it does

A student sits down before a placement drive and asks: **"I have a company
test/JD in front of me and N days left — what do I actually study?"**

Fast Prep answers with a **day-by-day study plan** built from three inputs:

| Input | Required? | What it tells us |
|---|---|---|
| **Company name** | At least one of the two | Past interview questions, round structure, what the company actually asks |
| **JD PDF** | At least one of the two | The exact skills/role they're hiring for |
| **Days left** | Always | How much we can realistically cover → plan density |

Either company name **or** JD alone works; both is best.

---

## 2. What the plan covers

The output is four **compartments**, always in this order:

### Compartment 1 — Most-asked interview questions (always present, separate)

The "seniors / people who actually sat the interview" compartment. Drawn
exclusively from `interview_experience` chunks of that company in the corpus
(real students' interview write-ups), **frequency-ranked**:

- Same question appearing across multiple experiences = higher rank ("asked in
  4/6 interviews").
- Near-duplicates ("difference between inner and left join" vs "INNER vs LEFT
  JOIN") are merged and their counts summed.
- Every question carries its **source citation** (file + page) so the student
  can open the original interview write-up.
- **Always present even if the user only uploaded a JD** — company is required,
  so we can always query past experiences. If the company has zero corpus data,
  we say so honestly and fall back to JD-driven questions (see §6, decision 4).

```json
"interview_questions": [
  {
    "question": "Explain the difference between INNER JOIN and LEFT JOIN with an example",
    "asked_in": 4,            // appeared in 4 of the interviewed students' write-ups
    "round": "Technical",
    "source": { "file": "ProcDNA_IV_1.pdf", "page": 3 }
  }
]
```

### Compartment 2 — Core subjects (the "core subs"), exact concepts

Role/company-aware, chosen from JD keywords **and** what the company's past
questions hit. **Aptitude is removed** — no aptitude study material, no
aptitude retrieval.

Every concept below is a **must-know** and ships with **its own clickable
reference link** — not one link per bucket, but one link per concept, so a
student can tap "INNER vs LEFT JOIN" and land directly on that topic's
reference (GeeksforGeeks article, official docs, or a well-known explainer).

| Bucket | Exact concepts we name (each is a must-know, each carries its own link) |
|---|---|
| **OOPS** | Classes vs objects, inheritance, polymorphism (compile vs runtime), encapsulation, abstraction, interfaces vs abstract classes, method overloading vs overriding, constructors, garbage collection |
| **DBMS** | SQL joins (INNER/LEFT/RIGHT/FULL), GROUP BY/HAVING, normalization 1NF–3NF, indexes (clustered vs non-clustered), transactions + ACID, primary vs foreign key, subqueries vs CTEs |
| **OS** | Processes vs threads, deadlock (conditions + prevention), scheduling (FCFS/SJF/RR), paging vs segmentation, memory management, race conditions + locks |
| **Networks** | TCP vs UDP, TCP 3-way handshake, HTTP vs HTTPS, DNS, OSI model, IP addressing/subnetting, cookies vs sessions |
| **System design** | Always included now — companies ask it increasingly, even at fresher/entry level: scalability basics, load balancing, caching (Redis), SQL vs NoSQL + when to use each, database sharding/replication, CAP theorem, API design (REST), rate limiting, message queues, a simple "design URL shortener / design a chat app" walk-through. Depth scales with the role (fresher = concepts + one design; senior/full-stack = deeper trade-offs). |

Rendered as: each concept is a chip/pill the student can click through to its
reference. In the UI it reads like a checklist of **must-know** items — tick
them off as you study.

Selection rule: **DSA and System design are always included.** The other
buckets (OOPS, DBMS, OS, Networks) appear only if the JD or the company's past
questions reference them — we don't dump every bucket on everyone.

### Compartment 3 — DSA: exact problems to do

Not "practice DP" — **named problems**, one line each, with a practice link:

```
Day 2 — Arrays:
  • Two Sum            → LeetCode 1          (link)
  • Best Time to Buy & Sell Stock → LeetCode 121 (link)
  • Sliding Window Maximum → LeetCode 239    (link)
Day 4 — DP:
  • Climbing Stairs    → LeetCode 70         (link)
  • Longest Common Subsequence → LeetCode 1143 (link)
```

| Track | Patterns included (each maps to 3–5 named problems) |
|---|---|
| Arrays & Strings | Two-pointer, sliding window, prefix sum, hashing |
| Linked Lists / Stacks / Queues | Reversal, cycle detection, monotonic stack, BFS/DFS |
| Trees & Graphs | Traversals, BST, recursion, shortest path, topological sort |
| DP | 1D/2D DP, knapsack-family, LCS/LIS, memoization |
| Searching & Sorting | Binary search variants, sort + two-pointer |

Depth scales with days-left: 3 days → only the highest-yield patterns (arrays,
two-pointer, 1D DP); 30 days → the full track, one pattern per day.

### Compartment 4 — Day-by-day schedule

The LLM distributes Compartments 1–3 across `days_left`, front-loading the
most-asked questions and high-priority concepts, and reserving the **last 1–2
days for mock/revision** of the top interview questions.

---

## 2b. How the plan is presented — two tabs

Once the plan is generated, the Fast Prep page shows **two tabs**:

| Tab | Content |
|---|---|
| **📋 Study Plan** | The day-by-day schedule (Compartment 4) with the core concepts + DSA problems for each day, each with its links. "Here's what to do today." |
| **🔥 Top Questions** | The most-asked / top-occurring company interview questions (Compartment 1), frequency-ranked with their sources. "Here's what seniors actually got asked." |

Tab name options for the second one (pick one, or we settle at build time):
- **"Top Asked"** — short, clear
- **"Most Asked"** — direct
- **"Hot Questions"** — casual
- **"Recent Interviews"** — emphasizes freshness
- **"Asked Before"** — plain

The DSA problems and core concepts live **inside each day of the Study Plan
tab** (with their links), so the schedule is the single scrollable "what to
do" view, and Top Questions is the always-visible "what to expect" view.
Compartment 1's questions also re-appear in the schedule days where they're
assigned for mock/revision, cross-linked back to the Top Questions tab.

---

## 3. Links — where they come from (your question)

Three kinds of links, clearly labelled in the UI:

| Kind | What it points to | Source |
|---|---|---|
| **Source citation** | The original interview write-up or JD chunk (file + page) behind every company interview question and every "why this concept" claim | Corpus — always available, opens the actual PDF page |
| **Practice links** | Every named DSA problem → its LeetCode / GeeksforGeeks problem page | Generated (curated problem → URL mapping) |
| **Concept links** | **Every** core concept (a must-know) → its own reference (GfG article, official docs, well-known explainer). One link per concept, not per bucket. | Generated (concept → best reference URL) |

So: every interview question is **backed by a clickable source**, every DSA
problem is **a clickable problem**, every concept is **a clickable reference**.
(Optional future: live web links via Google grounding, same as About Company —
see §6 decision 5.)

---

## 4. Inputs → plan generation (end-to-end flow)

```
        ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
        │ Company name│   │  JD PDF     │   │  Days left  │
        └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
               │                 │                 │
               ▼                 ▼                 ▼
   ┌────────────────────┐  ┌──────────────┐  ┌──────────────┐
   │ 1. Company lookup  │  │ 2. JD parse  │  │ 3. Days clamp│
   │   /companies/{name}│  │  (same as    │  │  1-90, tune  │
   │  → rounds, skills  │  │  resume/jd)  │  │  density     │
   └─────────┬──────────┘  └──────┬───────┘  └──────┬───────┘
             └────────────────────┼──────────────────┘
                                  ▼
              ┌──────────────────────────────────────────┐
              │ 4. RAG retrieval (existing retriever)    │
              │   - doc_type="interview_experience" +    │
              │     company=<name> → past questions      │
              │     (frequency-counted, deduped)         │
              │   - doc_type="job_description" → skills  │
              └──────────────────┬───────────────────────┘
                                 ▼
              ┌──────────────────────────────────────────┐
              │ 5. Gemini plan builder (one call)        │
              │   Inputs: interview questions + JD       │
              │   skills + days_left                     │
              │   Output: structured JSON (4 compartments)│
              └──────────────────┬───────────────────────┘
                                 ▼
              ┌──────────────────────────────────────────┐
              │ 6. Response: interview questions + core  │
              │    concepts + DSA problems + schedule    │
              └──────────────────────────────────────────┘
```

Aptitude is fully out: no `aptitude_material` query, no aptitude bucket, no
aptitude schedule entries. If past interviews mention an aptitude round, it
only appears as a **heads-up line** in round structure ("Round 1: Aptitude —
expect speed-based questions"), never as study material.

---

## 5. API design

### `POST /api/fast-prep/plan`
```json
{
  "company": "ProcDNA",          // optional, but at least one of company/JD
  "jd_file": "<multipart PDF>",  // optional
  "days_left": 14                // required, 1-90
}
```

### Response (drives the two tabs)

`interview_questions` feeds the **Top Questions** tab; `schedule` (with its
embedded concepts + DSA) feeds the **Study Plan** tab.

```json
{
  "company": "ProcDNA",
  "role": "Data Analyst",
  "days_left": 14,
  "density": "moderate",

  // ── Top Questions tab ──
  "interview_questions": [
    { "question": "SQL JOIN question from 4 interviews...",
      "asked_in": 4, "round": "Technical",
      "source": { "file": "ProcDNA_IV_1.pdf", "page": 3 } }
  ],

  // ── Study Plan tab: concepts + DSA embedded per day ──
  "core_concepts": [
    { "bucket": "DBMS", "priority": "high",
      "concepts": [
        { "name": "INNER vs LEFT JOIN", "link": "https://...gfg..." },
        { "name": "normalization 1NF-3NF", "link": "https://...gfg..." }
      ],
      "why": "JD lists SQL + 4 past questions mention joins" },
    { "bucket": "System design", "priority": "high",
      "concepts": [
        { "name": "load balancing", "link": "https://..." },
        { "name": "design URL shortener", "link": "https://..." }
      ],
      "why": "asked increasingly even at entry level" }
  ],
  "dsa": [
    { "day": 2, "pattern": "Arrays — two-pointer",
      "problems": [ { "name": "Two Sum", "platform": "LeetCode",
                      "id": 1, "link": "https://leetcode.com/problems/two-sum/" } ] }
  ],
  "schedule": [
    { "day": 1, "focus": "Most-asked SQL + Arrays",
      "concepts": ["INNER vs LEFT JOIN"], "dsa": ["Two Sum"],
      "revise_questions": ["ProcDNA SQL JOIN question"] }
  ]
}
```

---

## 6. Files touched (when we build)

| Layer | File | Change |
|---|---|---|
| Backend module | `backend/rag/fast_prep.py` (new) | JD parse + retrieval + question frequency-count + Gemini JSON |
| Schema | `backend/api/schemas.py` | `FastPrepRequest`, `FastPrepResponse`, sub-models per compartment |
| Route | `backend/api/routes.py` | `POST /api/fast-prep/plan` |
| Frontend | `frontend/src/pages/FastPrepPage.jsx` | form (company + JD upload + days slider) → two-tab render (Study Plan / Top Questions) |
| Services | `frontend/src/services/api.js` | `getFastPrepPlan()` |
| Styles | `frontend/src/index.css` | plan/schedule styling |

### Reused pieces (no new work)
- PDF text extraction — copy fitz `_extract_text` from `backend/resume/analyzer.py`
- JD skills/role extraction — same Gemini JSON approach as the resume analyzer
- Hybrid retrieval — `backend/rag/retriever.py` with company + doc_type filters
- Frequency-counting/dedup of interview questions — done in Python over
  retrieved chunks (no LLM needed for the count, LLM only for final shaping)

---

## 7. Decisions to confirm

1. **JD optional?** Plan says "at least one of company/JD". Pure-company plans
   work but are generic-er. Confirm.
2. **Density tiers** — 14 days: `packed` (6+ hrs/day), `moderate` (3-4),
   `relaxed` (1-2). Confirm.
3. **Question frequency cap** — Compartment 1 shows the top ~15 questions
   ranked by `asked_in`? Or all of them? (Plan: top 15, "see all" toggle.)
4. **No corpus data for a company** → graceful fallback: JD-only plan + a
   clear "no past interview write-ups ingested for X yet" note? Or auto-add a
   web-grounded "recent hiring pattern" section like About Company?
5. **Web grounding at all?** Keep Fast Prep 100% corpus-based (fast, free,
   offline) or optionally pull live links (slower, needs quota) — same tradeoff
   as About Company.
6. **No scores/ratings on the company** — the plan recommends *what to study*,
   never rates the company. (Confirmed behavior, carried over.)
7. **Day numbering** — "14 days left" → Day 1 today, Day 14 = light
   revision/mock. Confirm.
