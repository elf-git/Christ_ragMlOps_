import json
from urllib.request import Request, urlopen
from app.config import OLLAMA_MODEL, OLLAMA_URL
from app.ingest import build_index
from app.llm import SYSTEM
from app.retrieval import Retriever

query = "What are the library opening hours?"
passages, _ = Retriever(build_index()).search(query, limit=3)
context = "\n\n".join(f"[{i}] {p['doc']} PDF page {p['page']}\n{p['text']}" for i, p in enumerate(passages, 1))
payload = json.dumps({"model": OLLAMA_MODEL, "stream": False, "options": {"temperature": .1, "num_ctx": 4096, "num_predict": 220}, "prompt": f"{SYSTEM}\n\nCite source numbers in square brackets at the end of each sentence, for example: The library is open on Sunday. [1]\n\nSOURCE EXCERPTS\n{context}\n\nSTUDENT QUESTION\n{query}\n\nWrite 1-3 sentences with a citation after each sentence:"}).encode()
with urlopen(Request(f"{OLLAMA_URL}/api/generate", data=payload, headers={"Content-Type":"application/json"}), timeout=90) as response:
    data = json.load(response)
print(repr(data.get("response")))
