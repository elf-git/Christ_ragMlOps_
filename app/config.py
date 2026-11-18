from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"
INDEX = DATA / "index.json"
EMBEDDINGS = DATA / "embeddings.npy"
METRICS = DATA / "metrics.sqlite3"
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
DOCS = {
    "handbook": {"filename": "Student_Handbook.pdf", "title": "Christite Handbook 2026–27"},
    "calendar": {"filename": "ACADEMIC CALENDAR 2026-2027.pdf", "title": "Academic Calendar 2026–27"},
}
