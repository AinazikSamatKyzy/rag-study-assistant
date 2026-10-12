"""Measure retrieval quality: does the slide holding the answer show up in the top chunks?"""

import sys

from query_notes import TOP_K, load_vectorstore

# (question, slides that contain the answer). Questions are phrased the way a
# student would ask, not copied from the slides, so the test is realistic.
TEST_CASES = [
    ("What does a MAN connect?", {4}),
    ("What topology does a metropolitan network usually use?", {5, 6}),
    ("What is the difference between metro access and metro core?", {6}),
    ("Which IEEE standard defined DQDB and how fast was it?", {7}),
    ("How does a node get permission to send in DQDB?", {8}),
    ("What do the busy and request bits in a DQDB slot mean?", {9}),
    ("What speeds did SMDS support?", {10}),
    ("What does an add-drop multiplexer do?", {12}),
    ("Why does TDM waste bandwidth for bursty data traffic?", {14, 15}),
    ("What is Metro Ethernet and why use it?", {18}),
    ("What is the difference between full mesh and partial mesh?", {21}),
    ("How are voice and video prioritized in Metro Ethernet?", {22, 24}),
    ("What is the difference between wrap and steering in RPR?", {26}),
]


def evaluate() -> None:
    vectorstore = load_vectorstore()
    hits = 0
    for question, expected in TEST_CASES:
        results = vectorstore.similarity_search(question, k=TOP_K)
        # PyPDFLoader pages are 0-based; slide numbers are 1-based.
        got = [doc.metadata["page"] + 1 for doc in results]
        hit = bool(expected & set(got))
        hits += hit
        mark = "PASS" if hit else "MISS"
        print(f"{mark}  {question}\n      expected {sorted(expected)}, got {got}")

    total = len(TEST_CASES)
    print(f"\nHit rate @ top {TOP_K}: {hits}/{total} ({hits / total:.0%})")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    evaluate()
