# LLMOps & Observability

This document describes the MLOps and LLMOps practices implemented in this project to ensure reliability, observability, data integrity, and reproducibility.

---

## 1. Pillars of LLMOps in this Project

```
+---------------------------------------------------------------------------+
|                               LLMOps Pillars                              |
+---------------------+---------------------+-------------------------------+
|  1. Data Integrity  |  2. Privacy-First   | 3. Continuous Evaluation      |
|  & Drift Detection  |     Telemetry       |    & Benchmarking             |
|                     |                     |                               |
|  - SHA-256 Hashing  |  - No PII logged    |  - Automated Recall@5 tests   |
|  - Auto-reindexing  |  - SQLite storage   |  - Ground truth validation    |
|  - Cache management |  - Latency tracking |  - Zero-drift CI-ready runner |
+---------------------+---------------------+-------------------------------+
```

---

## 2. Document Integrity & Cache Invalidation

One of the most frequent operational failure modes in RAG systems is **index drift**—where source documents are updated, but the vector store or chunk index retains outdated references.

### Implementation (`app/ingest.py`)
- Every source PDF is hashed via SHA-256 upon application startup:
  ```python
  def signature() -> dict[str, str]:
      return {
          key: hashlib.sha256((SOURCES / doc["filename"]).read_bytes()).hexdigest()
          for key, doc in DOCS.items()
      }
  ```
- If the signature does not match `data/index.json`, the index is rebuilt from scratch and any existing vector embeddings (`data/embeddings.npy`) are automatically deleted and recomputed.

---

## 3. Privacy-Preserving Runtime Telemetry (`app/ops.py`)

Student inquiries often include sensitive personal context. To maintain strict data privacy while still achieving high operational visibility, the system stores **telemetry without storing questions or generated answers**.

### Stored Schema
```sql
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    retrieval_ms INTEGER NOT NULL,
    generation_ms INTEGER NOT NULL,
    retrieval_mode TEXT NOT NULL,     -- 'hybrid' or 'bm25'
    answer_mode TEXT NOT NULL,        -- 'source', 'extractive', or model name
    source_count INTEGER NOT NULL,
    feedback INTEGER CHECK (feedback IN (-1, 1))
);
```

### Metrics Provided (`/api/status`)
- Total queries served
- Average retrieval latency ($\text{ms}$)
- Average generation latency ($\text{ms}$)
- Aggregate positive (`+1`) and negative (`-1`) user ratings

---

## 4. Automated Retrieval Quality Evaluation (`app/evaluate.py`)

Retrieval performance directly bounds RAG quality: if relevant context is not in top-$K$, generation is guaranteed to fail or hallucinate.

### The Evaluation Test Suite
The evaluation script validates top-5 retrieval accuracy across representative queries covering both documents:

| Query | Document | Expected PDF Page(s) |
|---|---|---|
| *What are the library opening hours?* | Handbook | 18 |
| *How can students renew library books online?* | Handbook | 22 |
| *How do I apply for a fee concession?* | Handbook | 82, 83 |
| *What is the university's policy on ragging?* | Handbook | 96, 97, 98, 99 |
| *What are the requirements for international students?* | Handbook | 85 |
| *When are the August 2026 mid semester exams?* | Calendar | 6 |
| *When is the May Day holiday in 2027?* | Calendar | 15 |
| *How many instructional days are in the odd semester?* | Calendar | 16 |

### Running the Evaluation
```powershell
python -m app.evaluate
```

Output:
```
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

---

## 5. Failure Modes & Graceful Degradation

| Failure Condition | System Response | User Impact |
|---|---|---|
| Ollama server is stopped | Detects failure in $\le 2\text{s}$, switches to extractive answering | Accurate factual answer from source PDF, zero downtime |
| GPU unavailable | Sentence-transformers runs seamlessly on CPU; falls back to pure BM25 if model absent | System functions with negligible latency impact |
| Student asks for specific dates or fees | Precision query guard serves exact contiguous text | Prevents LLM numerical hallucinations |
| Malicious prompt injection in PDF | System prompt designates sources as untrusted data | Prevents prompt override attacks |
