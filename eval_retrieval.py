"""Measure retrieval quality: does the page holding the answer show up in the top chunks?

Usage:
    python eval_retrieval.py                                   # bundled Kubernetes notes
    python eval_retrieval.py eval/metro_ethernet.json          # your own notes + cases
    python eval_retrieval.py --min-hit-rate 0.85               # exit 1 below threshold (CI)
"""

import argparse
import json
import sys
from pathlib import Path

from query_notes import TOP_K, load_vectorstore

DEFAULT_CASES = Path(__file__).resolve().parent / "eval" / "kubernetes_notes.json"


def evaluate(cases_path: Path) -> float:
    # Each case is a question plus the pages that contain the answer. Questions are
    # phrased the way a student would ask, not copied from the notes, so the test is realistic.
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    vectorstore = load_vectorstore()
    hits = 0
    for case in cases:
        expected = set(case["pages"])
        results = vectorstore.similarity_search(case["question"], k=TOP_K)
        # PyPDFLoader pages are 0-based; page numbers in the cases are 1-based.
        got = [doc.metadata["page"] + 1 for doc in results]
        hit = bool(expected & set(got))
        hits += hit
        mark = "PASS" if hit else "MISS"
        print(f"{mark}  {case['question']}\n      expected {sorted(expected)}, got {got}")

    rate = hits / len(cases)
    print(f"\nHit rate @ top {TOP_K}: {hits}/{len(cases)} ({rate:.0%})")
    return rate


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("cases", nargs="?", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--min-hit-rate", type=float, default=0.0,
                        help="fail (exit 1) if the hit rate is below this, e.g. 0.85")
    args = parser.parse_args()

    rate = evaluate(args.cases)
    if rate < args.min_hit_rate:
        print(f"FAILED: hit rate {rate:.0%} is below the required {args.min_hit_rate:.0%}")
        sys.exit(1)
