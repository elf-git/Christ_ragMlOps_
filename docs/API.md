# API Reference

The CHRIST Student Desk backend is built with FastAPI. All endpoints are served at `http://127.0.0.1:8000`.

---

## Interactive Documentation
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## Endpoints

### 1. System Status
`GET /api/status`

Returns index readiness, document metadata, vector embedding state, Ollama model availability, and aggregate operational metrics.

#### Response `200 OK`
```json
{
  "documents": [
    {
      "id": "handbook",
      "title": "Christite Handbook 2026–27",
      "pages": 110
    },
    {
      "id": "calendar",
      "title": "Academic Calendar 2026–27",
      "pages": 20
    }
  ],
  "passages": 291,
  "embeddings_ready": true,
  "embedding_error": null,
  "llm_ready": false,
  "llm_model": "qwen2.5:1.5b",
  "metrics": {
    "queries": 14,
    "avg_retrieval_ms": 12,
    "avg_generation_ms": 35,
    "positive_feedback": 8,
    "negative_feedback": 1
  }
}
```

---

### 2. Chat Query
`POST /api/chat`

Submits a student question to the RAG pipeline. Returns the grounded or extractive answer, verified source citations, and latency telemetry.

#### Request Body
```json
{
  "question": "What are the library opening hours?"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | string | Yes | Query string (3 to 800 characters) |

#### Response `200 OK`
```json
{
  "answer": "From the source document:\n\nLibrary Hours: Central Library: Monday to Friday: 8:00 AM to 9:00 PM; Saturday: 8:00 AM to 6:00 PM; Sunday: 9:00 AM to 1:00 PM [1]\n\nOpen the cited PDF page to check the full context.",
  "answer_mode": "source",
  "sources": [
    {
      "number": 1,
      "title": "Christite Handbook 2026–27",
      "doc": "handbook",
      "page": 18,
      "excerpt": "Library Hours: Central Library: Monday to Friday: 8:00 AM to 9:00 PM...",
      "url": "/api/source/handbook#page=18"
    }
  ],
  "run_id": 15,
  "retrieval_ms": 14,
  "generation_ms": 2
}
```

---

### 3. User Feedback
`POST /api/feedback`

Records student feedback (helpful/unhelpful) for a specific run ID into the telemetry store.

#### Request Body
```json
{
  "run_id": 15,
  "helpful": true
}
```

#### Response `200 OK`
```json
{
  "ok": true
}
```

#### Error Response `404 Not Found`
```json
{
  "detail": "Run not found"
}
```

---

### 4. PDF Source Viewer
`GET /api/source/{doc_id}`

Streams the original source PDF inline to allow students to verify exact context and page anchors.

#### Path Parameters
| Parameter | Type | Values |
|---|---|---|
| `doc_id` | string | `handbook` or `calendar` |

#### Response `200 OK`
Content-Type: `application/pdf`
Inline browser stream.
