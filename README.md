Markdown
# EPCDash: AI-Powered Multi-Agent Ingestion Platform for Construction Operations

An intelligent, schema-driven multi-agent platform designed to automate data extraction, validation, and real-time ledger synchronization for large-scale EPC (Engineering, Procurement, and Construction) turnkey projects. 

By replacing manual site log processing, this platform eliminates administrative overhead and ingestion latency by transforming unstructured daily site logs (WhatsApp images, document fragments, multi-page reports) into production-grade data streams.

## 🏗️ System Architecture & Multi-Agent Workflow
The platform is powered by an orchestrated **LangGraph** pipeline that models ingestion as a state machine, moving data through isolated processing steps to ensure zero data loss and strict validation:

1. **Ingestion & Dynamic Batching Node:** Computes deterministic SHA-256 batch signatures over multi-image sequences (e.g., consecutive WhatsApp photos representing a single day's site log) to guarantee atomicity and avoid parent record duplication.
2. **Schema-Driven Extraction Node (Parallelized LLM Passes):** Orchestrates parallel execution runs using **Gemini Pro Vision** based on checked categories (`DPR`, `MATERIAL`, `BILLING`, `DRAWING`). If a category is omitted, extraction skips it to optimize token overhead.
3. **Structured Validation Node:** Parses structural text and maps it into Pydantic models to cross-reference extracted metrics (labor headcounts, cement/steel consumption metrics) against deterministic corporate rules.
4. **Excel Writer Engine:** Dynamically injects clean data into targeted columns and sheets (e.g., `Daily_Progress_Log`, `Material_Ledger`) using sheet metadata maps (`header_row`, `data_start_row`), enabling real-time writes into working operational files.

## 🛠️ Tech Stack
* **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS
* **Backend Framework:** FastAPI, Uvicorn
* **Agent Orchestration:** LangGraph, LangChain
* **Core AI Models:** Gemini Pro Vision (Multimodal Extraction)
* **Database & Persistence:** SQLite, SQLAlchemy ORM
* **Data Processing:** Python, Pandas, OpenPyXL

## ✨ Key Features Implemented
* **Multi-Image Continuous Context:** Stages and sequences multiple physical images into an ordered visual context array for the multimodal LLM, extracting a single cohesive operational record.
* **Chronological Timeline Grouping:** Dynamically reorganizes flat document streams into a scannable, collapsible archive grouped by the **true operational date** read inside the log, rather than machine upload timestamps.
* **Full-Stack Orphan-Safe Purging:** A safe, cascading deletion API that deep-cleans corresponding SQLite rows and handles multi-category physical file structures safely without breaking shared asset dependencies.

## 🚀 Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18+
* Gemini API Key

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
Create and activate a virtual environment:
Bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:
Bash
pip install -r requirements.txt
Run the development server:
Bash
./run_backend.sh
Frontend Setup
Navigate to the frontend directory:
Bash
cd ../frontend
Install packages:
Bash
npm install
Start the Next.js app:
Bash
npm run dev

***