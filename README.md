# 🏗️ EPCdash: Enterprise EPC Project Command Center

## Executive Overview
In multi-crore Engineering, Procurement, and Construction (EPC) operations, a critical fragmentation exists between on-site physical engineering schedules (typically tracked in isolated Excel workbooks) and formal client billing structures dictated by complex Tender Agreement tranches. This repository serves as a production-grade, AI-powered command center designed to bridge that gap. By unifying unstructured site data, conversational inputs, and rigid financial ledgers, the platform provides real-time operational visibility and automated cash flow auditing for principal contractors.

## Core Architecture Highlights
- **Decoupled Bi-Layer Event Model:** Engineered a strict separation of concerns between pure physical progress strings and relational payment tranches (`PaymentMilestone`). This guarantees absolute data integrity and state preservation, even during schema-safe, destructive Excel master-schedule re-uploads.
- **Intelligent Asynchronous Workflows:** Built a provider-agnostic, automated outbound WhatsApp alert infrastructure paired with an inbound, state-driven LLM parsing engine (powered by Google Gemini Flash). The system dynamically ingests informal operational texts and translates them into formal, institutional-grade client correspondence and actionable database mutations.
- **Dynamic Financial Auditing UI:** Developed an enterprise-focused cash flow summary dashboard. Features include real-time tracking of top-line contract values, automated lightweight SQLite column retrofitting to capture daily miscellaneous out-of-pocket leakage, and live, reactive "Uninvoiced Work Value" calculations to optimize billing cycles.
- **Resilient Infrastructure:** Architected a production-ready, multi-service deployment model (FastAPI backend, Next.js frontend) featuring idempotent startup data hydration hooks, robust API retry mechanisms with exponential backoff, and in-memory raw-text caching for optimized LLM context window management.

## ⚙️ System Architecture & Multi-Agent Workflow
The platform is powered by an orchestrated **LangGraph** pipeline that models ingestion as a state machine, moving data through isolated processing steps to ensure zero data loss and strict validation:

1. **Ingestion & Dynamic Batching Node:** Computes deterministic SHA-256 batch signatures over multi-image sequences (e.g., consecutive WhatsApp photos representing a single day's site log) to guarantee atomicity and avoid parent record duplication.
2. **Schema-Driven Extraction Node (Parallelized LLM Passes):** Orchestrates parallel execution runs using **Gemini Flash** based on checked categories (`DPR`, `MATERIAL`, `BILLING`, `DRAWING`). If a category is omitted, extraction skips it to optimize token overhead.
3. **Structured Validation Node:** Parses structural text and maps it into Pydantic models to cross-reference extracted metrics (labor headcounts, cement/steel consumption metrics) against deterministic corporate rules.
4. **Excel Writer Engine:** Dynamically injects clean data into targeted columns and sheets (e.g., `Daily_Progress_Log`, `Material_Ledger`) using sheet metadata maps (`header_row`, `data_start_row`), enabling real-time writes into working operational files.

## 🛠️ Tech Stack
* **Frontend:** Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Recharts
* **Backend Framework:** FastAPI, Uvicorn
* **Agent Orchestration:** LangGraph, LangChain
* **Core AI Models:** Google Gemini 2.5 Flash (Multimodal Extraction & GraphRAG)
* **Database & Persistence:** SQLite, SQLAlchemy ORM
* **Data Processing:** Python, Pandas, OpenPyXL, PyPDF

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18+
* Gemini API Key (`GEMINI_API_KEY`)

### Local Development
1. **Backend Setup:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn backend.main:app --port 8000 --reload
   ```

2. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
