"""Minimal local LLMOps: privacy-conscious run metrics and feedback."""
import sqlite3
from datetime import datetime, timezone

from .config import METRICS


def connect():
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(METRICS)
    db.execute("""CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        retrieval_ms INTEGER NOT NULL,
        generation_ms INTEGER NOT NULL,
        retrieval_mode TEXT NOT NULL,
        answer_mode TEXT NOT NULL,
        source_count INTEGER NOT NULL,
        feedback INTEGER CHECK (feedback IN (-1,1))
    )""")
    return db


def log_run(retrieval_ms, generation_ms, retrieval_mode, answer_mode, source_count):
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO runs (created_at,retrieval_ms,generation_ms,retrieval_mode,answer_mode,source_count) VALUES (?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), retrieval_ms, generation_ms, retrieval_mode, answer_mode, source_count),
        )
        return cursor.lastrowid


def log_feedback(run_id: int, value: int):
    with connect() as db:
        cursor = db.execute("UPDATE runs SET feedback=? WHERE id=?", (value, run_id))
        return cursor.rowcount > 0


def summary():
    with connect() as db:
        row = db.execute("SELECT count(*), round(avg(retrieval_ms)), round(avg(generation_ms)), sum(feedback=1), sum(feedback=-1) FROM runs").fetchone()
    return {"queries": row[0], "avg_retrieval_ms": row[1] or 0, "avg_generation_ms": row[2] or 0, "positive_feedback": row[3] or 0, "negative_feedback": row[4] or 0}
