"""Small reproducible retrieval smoke evaluation over the supplied PDFs.

Run: python -m app.evaluate
The expected pages were manually checked against the source PDFs.
"""
from .ingest import build_index
from .retrieval import Retriever

CASES = [
    ("What are the library opening hours?", "handbook", {18}),
    ("How can students renew library books online?", "handbook", {22}),
    ("How do I apply for a fee concession?", "handbook", {82, 83}),
    ("What is the university's policy on ragging?", "handbook", {96, 97, 98, 99}),
    ("What are the requirements for international students?", "handbook", {85}),
    ("When are the August 2026 mid semester exams?", "calendar", {6}),
    ("When is the May Day holiday in 2027?", "calendar", {15}),
    ("How many instructional days are in the odd semester?", "calendar", {16}),
]


def main():
    retriever = Retriever(build_index())
    hits = 0
    for question, doc, pages in CASES:
        found, _ = retriever.search(question)
        hit = any(x["doc"] == doc and x["page"] in pages for x in found)
        hits += hit
        print(f"{'PASS' if hit else 'MISS'}  {question}")
        if not hit:
            print("      ", [(x["doc"], x["page"]) for x in found])
    print(f"Recall@5: {hits}/{len(CASES)} ({hits/len(CASES):.0%})")
    raise SystemExit(0 if hits == len(CASES) else 1)


if __name__ == "__main__":
    main()
