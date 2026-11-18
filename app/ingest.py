"""Page-aware PDF ingestion. PDF text is data, never executable instructions."""
import hashlib
import json
import re
from pathlib import Path

from pypdf import PdfReader

from .config import DOCS, EMBEDDINGS, INDEX, SOURCES


def clean_text(value: str) -> str:
    value = value.replace("\ufffd", "-").replace("\u00ad", "")
    value = re.sub(r"[\t ]+", " ", value)
    value = re.sub(r"\n\s*\n+", "\n", value)
    return value.strip()


def split_page(text: str, limit: int = 1150, overlap: int = 160) -> list[str]:
    # Preserve page boundaries so every cited passage has an exact PDF page.
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    chunks, current = [], ""
    for line in lines:
        if len(line) > limit:
            pieces = [line[i:i + limit] for i in range(0, len(line), limit - overlap)]
        else:
            pieces = [line]
        for piece in pieces:
            if current and len(current) + len(piece) + 1 > limit:
                chunks.append(current)
                current = current[-overlap:] + "\n" + piece
            else:
                current = f"{current}\n{piece}".strip()
    if current:
        chunks.append(current)
    return chunks


def signature() -> dict[str, str]:
    return {
        key: hashlib.sha256((SOURCES / doc["filename"]).read_bytes()).hexdigest()
        for key, doc in DOCS.items()
    }


def build_index() -> dict:
    SOURCES.mkdir(parents=True, exist_ok=True)
    missing = [doc["filename"] for doc in DOCS.values() if not (SOURCES / doc["filename"]).exists()]
    if missing:
        raise FileNotFoundError("Missing source PDFs in data/sources: " + ", ".join(missing))

    sig = signature()
    if INDEX.exists():
        try:
            old = json.loads(INDEX.read_text(encoding="utf-8"))
            if old.get("signature") == sig and old.get("version") == 1:
                return old
        except (ValueError, OSError):
            pass

    chunks, pages = [], {}
    for key, doc in DOCS.items():
        reader = PdfReader(str(SOURCES / doc["filename"]))
        pages[key] = len(reader.pages)
        for page_number, page in enumerate(reader.pages, 1):
            text = clean_text(page.extract_text() or "")
            for ordinal, passage in enumerate(split_page(text)):
                if len(passage) < 50:
                    continue
                chunks.append({
                    "id": f"{key}-{page_number}-{ordinal}",
                    "doc": key,
                    "page": page_number,
                    "text": passage,
                })

    output = {"version": 1, "signature": sig, "pages": pages, "chunks": chunks}
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(output, ensure_ascii=False), encoding="utf-8")
    # Any previous vectors refer to different chunk positions.
    EMBEDDINGS.unlink(missing_ok=True)
    return output


if __name__ == "__main__":
    result = build_index()
    print(f"Indexed {len(result['chunks'])} passages from {result['pages']}")
