# CHRIST Student Desk · Grounded RAG & LLMOps Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![RAG Evaluation](https://img.shields.io/badge/Recall%405-100%25-brightgreen.svg)](#retrieval-evaluation)
[![Ollama](https://img.shields.io/badge/LLM-Qwen2.5%201.5B-orange.svg)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A privacy-first, locally deployable student helpdesk and RAG platform grounded in the official **Christite Handbook 2026–27** and **Academic Calendar 2026–27**.

Designed from the ground up to showcase three interconnected GenAI and MLOps engineering concepts:

| Concept | Implementation | Engineering Benefit |
|---|---|---|
| **RAG** | Page-aware PDF ingestion, BM25 lexical + MiniLM semantic vectors, Reciprocal Rank Fusion (RRF), exact PDF-page citations. | Prevents hallucinations by strictly grounding answers in university source documents with direct page links. |
| **Local LLM** | Qwen 2.5 1.5B running on local Ollama instance with low-temperature constrained prompt synthesis. | Cost-effective, privacy-preserving, and runs completely on consumer hardware without external API reliance. |
| **LLMOps** | SHA-256 source hashing, automatic reindexing on drift, query precision gating, local SQLite telemetry, and automated retrieval benchmarking. | Observable latencies, user feedback loops, zero index staleness, and reproducible retrieval evaluation. |

---

## Architecture Overview

```
+-----------------------------------------------------------------------------------+
|                                  USER / CLIENT                                    |
|              Modern Web Interface (Vanilla HTML5 / CSS3 / ES6)                     |
+----------------------------------------+------------------------------------------+
                                         |  HTTP /api/chat
                                         v
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                    |
|                                                                                   |
|  +------------------------+  +------------------------+  +---------------------+  |
|  |     Ingestion &        |  |    Hybrid Retrieval    |  |     Synthesis &     |  |
|  |      Integrity         |  |         Engine         |  |      Guardrails     |  |
|  |                        |  |                        |  |                     |  |
|  | * SHA-256 validation   |  | * BM25 lexical scoring |  | * Precision query   |  |
|  | * Page-aware chunking  |  | * all-MiniLM-L6-v2     |  |   guard (extractive)|  |
|  | * Auto-reindexing on   |  | * Reciprocal Rank      |  | * Ollama Qwen2.5    |  |
|  |   document updates     |  |   Fusion (RRF)         |  | * Citation validator|  |
|  +------------------------+  +------------------------+  +---------------------+  |
|                                         |                                         |
|                                         v                                         |
|  +-----------------------------------------------------------------------------+  |
|  |                             LLMOps & Telemetry                              |  |
|  |  * SQLite run metrics (retrieval_ms, generation_ms, answer_mode, feedback)  |  |
|  |  * Privacy-preserving (Zero PII or question text stored)                    |  |
|  |  * Automated Retrieval Benchmark (python -m app.evaluate) -> 100% Recall@5  |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

Detailed technical documentation is available in [`docs/`](./docs/):
- **[System Architecture & Design Deep Dive](./docs/ARCHITECTURE.md)**
- **[LLMOps, Telemetry & Evaluation](./docs/LLMOPS.md)**
- **[API Specification & Endpoint Reference](./docs/API.md)**

---

## Key Features

- **Hybrid Retrieval with Reciprocal Rank Fusion**: Combines lexical search (BM25 with domain-specific tokenization) and semantic dense vectors (`all-MiniLM-L6-v2`) to capture exact campus terms and high-level conceptual questions.
- **Precision Query Guard**: Automatically detects queries concerning dates, deadlines, hours, fees, or marks, serving verbatim contiguous passages to prevent numerical LLM hallucinations.
- **Direct PDF Citations**: Every cited passage links directly to the corresponding page anchor (`#page=X`) in the embedded PDF viewer.
- **Extractive Fallback**: If Ollama is offline, the system seamlessly transitions to extractive source ranking without crashing or returning empty answers.
- **Local & Privacy-Conscious**: All embeddings, indexing, inference, and telemetry are executed locally on your machine. No student data or questions are logged or sent to third-party APIs.

---

## Project Structure

```
Christ_ragMlOps_/
├── app/
│   ├── __init__.py           # Package marker
│   ├── config.py             # Global paths and environment configuration
│   ├── evaluate.py           # Retrieval benchmark suite (Recall@5 evaluation)
│   ├── ingest.py             # Page-aware PDF ingestion, cleaning, and indexing
│   ├── llm.py                # Ollama client, grounded generation, and extractive fallback
│   ├── main.py               # FastAPI application with routing and lifespan handlers
│   ├── ops.py                # Telemetry logging and SQLite metrics aggregation
│   └── retrieval.py          # Hybrid retrieval (BM25 + Dense all-MiniLM-L6-v2 + RRF)
├── data/
│   └── sources/              # Canonical institutional PDFs
│       ├── ACADEMIC CALENDAR 2026-2027.pdf
│       └── Student_Handbook.pdf
├── docs/
│   ├── API.md                # REST API endpoint reference and examples
│   ├── ARCHITECTURE.md       # In-depth architectural flow and design decisions
│   └── LLMOPS.md             # LLMOps practices, data versioning, and telemetry
├── web/
│   ├── app.js                # Frontend client logic, state management, and stream UI
│   ├── index.html            # Responsive single-page application interface
│   └── styles.css            # Custom editorial styling and layout
├── .gitignore                # Production git ignore definitions
├── probe.py                  # Standalone probe script for quick inference testing
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## Getting Started

### Prerequisites

1. **Python 3.10 or higher**
2. **Ollama** (optional for LLM generation; the system falls back to extractive mode if Ollama is not installed):
   - Install from [ollama.com](https://ollama.com/)
   - Pull the recommended model:
     ```powershell
     ollama pull qwen2.5:1.5b
     ```

### 1. Installation

Clone this repository and install dependencies in your Python environment:

```powershell
git clone https://github.com/elf-git/Christ_ragMlOps_.git
cd Christ_ragMlOps_

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### 2. Verify Retrieval Pipeline

Run the automated evaluation benchmark to verify indexing and retrieval accuracy:

```powershell
python -m app.evaluate
```

Expected output:
```text
PASS  What are the library opening hours?
PASS  How can students renew library books online?
PASS  How do I apply for a fee concession?
PASS  What is the university's policy on ragging?
PASS  What are the requirements for international students?
PASS  When are the August 2026 mid semester exams?
PASS  When is the May Day holiday in 2027?
PASS  How many instructional days are in the odd semester?
Recall@5: 8/8 (100%)
```

### 3. Run the Application

Start the local server using Uvicorn:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## Configuration

The application can be configured via environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Endpoint for the local Ollama instance. |
| `OLLAMA_MODEL` | `qwen2.5:1.5b` | Model name pulled in Ollama. |
| `EMBED_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | SentenceTransformer model identifier for semantic embeddings. |

---

## LLMOps Telemetry & Monitoring

Access the runtime status and telemetry endpoint at:
```http
GET http://127.0.0.1:8000/api/status
```

Response includes:
- Source documents and indexed passage counts
- Vector embeddings and model availability status
- Total queries served
- Average retrieval latency (`avg_retrieval_ms`)
- Average generation latency (`avg_generation_ms`)
- Aggregate positive and negative student feedback

---

## Disclaimer

This project is an independent prototype developed for research and educational purposes using publicly available university handbook and calendar documents. It is not an official CHRIST (Deemed to be University) service. Students must always verify critical deadlines and academic regulations with the respective university offices and official notices.
