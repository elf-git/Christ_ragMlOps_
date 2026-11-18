"""Hybrid local retrieval: BM25 plus MiniLM embeddings when available."""
import math
import os
import re
from collections import Counter
from time import perf_counter

import numpy as np

from .config import EMBEDDINGS, EMBED_MODEL

STOP = set("a an and are as at be by can do for from how i in is it of on or the to what when where which who with you your university christ".split())


def terms(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1 and t not in STOP]


class Retriever:
    def __init__(self, index: dict):
        self.chunks = index["chunks"]
        self.tokens = [terms(c["text"]) for c in self.chunks]
        self.tf = [Counter(row) for row in self.tokens]
        self.lengths = [len(row) for row in self.tokens]
        self.avg_len = sum(self.lengths) / max(1, len(self.lengths))
        df = Counter()
        for row in self.tf:
            df.update(row.keys())
        n = len(self.chunks)
        self.idf = {t: math.log(1 + (n - f + .5) / (f + .5)) for t, f in df.items()}
        self.encoder = None
        self.vectors = None
        self.embedding_error = None
        self._load_embeddings()

    def _load_embeddings(self):
        try:
            # Local-only prevents a surprise network download on startup.
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("USE_TF", "0")
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer(EMBED_MODEL, local_files_only=True)
            if EMBEDDINGS.exists():
                vectors = np.load(EMBEDDINGS)
                if len(vectors) == len(self.chunks):
                    self.vectors = vectors
            if self.vectors is None:
                self.vectors = self.encoder.encode(
                    [c["text"] for c in self.chunks],
                    batch_size=32,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                )
                np.save(EMBEDDINGS, self.vectors)
        except Exception as exc:
            self.embedding_error = str(exc)
            self.encoder = None
            self.vectors = None

    def search(self, query: str, limit: int = 5) -> tuple[list[dict], dict]:
        start = perf_counter()
        q = terms(query)
        lexical = np.zeros(len(self.chunks), dtype=np.float32)
        for i, row in enumerate(self.tf):
            for term in q:
                freq = row.get(term, 0)
                if freq:
                    lexical[i] += self.idf.get(term, 0) * (freq * 2.2) / (
                        freq + 1.2 * (.25 + .75 * self.lengths[i] / self.avg_len)
                    )
        semantic = np.zeros_like(lexical)
        if self.encoder is not None and self.vectors is not None:
            qvec = self.encoder.encode([query], normalize_embeddings=True, convert_to_numpy=True)[0]
            semantic = self.vectors @ qvec

        # Reciprocal rank fusion tolerates incomparable raw score scales.
        fused = np.zeros_like(lexical)
        for scores, weight in ((lexical, 1.0), (semantic, 1.0 if self.vectors is not None else 0.0)):
            if weight and np.any(scores):
                for rank, idx in enumerate(np.argsort(scores)[::-1][:40]):
                    fused[idx] += weight / (60 + rank + 1)
        date_query = bool(re.search(r"\b(date|calendar|holiday|exam|semester|january|february|march|april|may|june|july|august|september|october|november|december|2026|2027)\b", query.lower()))
        if date_query:
            for i, chunk in enumerate(self.chunks):
                if chunk["doc"] == "calendar":
                    fused[i] *= 1.12
        # Page headings are often more informative than a long passage body.
        query_pairs = {f"{a} {b}" for a, b in zip(q, q[1:])}
        for i, chunk in enumerate(self.chunks):
            heading = " ".join(terms(chunk["text"][:220]))
            if any(pair in heading for pair in query_pairs):
                fused[i] += 0.02

        indices = np.argsort(fused)[::-1]
        results, seen = [], set()
        for i in indices:
            if fused[i] <= 0 or len(results) >= limit:
                break
            chunk = self.chunks[int(i)]
            page_key = (chunk["doc"], chunk["page"])
            if page_key in seen:
                continue
            seen.add(page_key)
            results.append({**chunk, "score": round(float(fused[i]), 5)})
        return results, {"retrieval_ms": round((perf_counter() - start) * 1000), "mode": "hybrid" if self.vectors is not None else "bm25"}
