from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import DOCS, OLLAMA_MODEL, ROOT, SOURCES
from .ingest import build_index
from .llm import answer, ollama_available
from .ops import log_feedback, log_run, summary
from .retrieval import Retriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    index = build_index()
    app.state.index = index
    app.state.retriever = Retriever(index)
    yield


app = FastAPI(title="CHRIST Student Desk", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=800)


class FeedbackRequest(BaseModel):
    run_id: int
    helpful: bool


@app.get("/api/status")
def status():
    retriever = app.state.retriever
    return {
        "documents": [{"id": k, "title": v["title"], "pages": app.state.index["pages"][k]} for k, v in DOCS.items()],
        "passages": len(app.state.index["chunks"]),
        "embeddings_ready": retriever.vectors is not None,
        "embedding_error": retriever.embedding_error,
        "llm_ready": ollama_available(),
        "llm_model": OLLAMA_MODEL,
        "metrics": summary(),
    }


@app.post("/api/chat")
def chat(body: ChatRequest):
    passages, retrieval = app.state.retriever.search(body.question, limit=4)
    response, mode, generation_ms = answer(body.question, passages)
    run_id = log_run(retrieval["retrieval_ms"], generation_ms, retrieval["mode"], mode, len(passages))
    sources = [{
        "number": i,
        "title": DOCS[p["doc"]]["title"],
        "doc": p["doc"],
        "page": p["page"],
        "excerpt": p["text"][:420],
        "url": f"/api/source/{p['doc']}#page={p['page']}",
    } for i, p in enumerate(passages, 1)]
    return {"answer": response, "answer_mode": mode, "sources": sources, "run_id": run_id, "retrieval_ms": retrieval["retrieval_ms"], "generation_ms": generation_ms}


@app.post("/api/feedback")
def feedback(body: FeedbackRequest):
    if not log_feedback(body.run_id, 1 if body.helpful else -1):
        raise HTTPException(404, "Run not found")
    return {"ok": True}


@app.get("/api/source/{doc_id}")
def source(doc_id: str):
    if doc_id not in DOCS:
        raise HTTPException(404, "Source not found")
    return FileResponse(SOURCES / DOCS[doc_id]["filename"], media_type="application/pdf", filename=DOCS[doc_id]["filename"], content_disposition_type="inline")


app.mount("/", StaticFiles(directory=ROOT / "web", html=True), name="web")
