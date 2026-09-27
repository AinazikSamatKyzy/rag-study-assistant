"""Search the existing Chroma notes database and print the top chunks."""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings

CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"
COLLECTION_NAME = "metro_ethernet_notes"
QUESTION = "What is Metro Ethernet?"
TOP_K = 3


def query_notes() -> None:
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"No Chroma database at {CHROMA_DIR}. Run ingest_notes.py first."
        )

    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    vectorstore = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )

    results = vectorstore.similarity_search(QUESTION, k=TOP_K)
    print(f"Question: {QUESTION}\n")
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
    query_notes()
