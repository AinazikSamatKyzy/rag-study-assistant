"""Search the existing Chroma notes database and print the top chunks."""

import os
import sys
from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

# Overridable so a container can keep the database on a mounted volume.
CHROMA_DIR = Path(os.environ.get("CHROMA_DIR", Path(__file__).resolve().parent / "chroma_db"))
COLLECTION_NAME = "study_notes"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_QUESTION = "What is a pod in Kubernetes?"
TOP_K = 3


# Cached so the web app loads the embedding model once, not on every question.
@lru_cache(maxsize=1)
def load_vectorstore() -> Chroma:
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"No Chroma database at {CHROMA_DIR}. Run ingest_notes.py first."
        )

    embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )


def query_notes(question: str) -> None:
    vectorstore = load_vectorstore()
    results = vectorstore.similarity_search(question, k=TOP_K)
    print(f"Question: {question}\n")
    if not results:
        print("No matching chunks found.")
        return

    for i, doc in enumerate(results, start=1):
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page")
        location = f"{source}" if page is None else f"{source} (page {page})"
        print(f"--- Chunk {i} | {location} ---")
        print(doc.page_content.strip())
        print()


if __name__ == "__main__":
    # Windows consoles may default to a legacy codepage that can't print PDF symbols.
    sys.stdout.reconfigure(encoding="utf-8")
    # Usage: python query_notes.py "your question here"
    question = " ".join(sys.argv[1:]).strip() or DEFAULT_QUESTION
    query_notes(question)
