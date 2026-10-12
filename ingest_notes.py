"""Load a lecture PDF, chunk it, and store it in local Chroma."""

import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Default PDF; pass a different path as an argument: python ingest_notes.py my_notes.pdf
PDF_PATH = Path(__file__).resolve().parent / "Chap3_Metro_Ethernet.pdf"
CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"
COLLECTION_NAME = "metro_ethernet_notes"


def ingest(pdf_path: Path) -> None:
    if not pdf_path.exists():
        raise FileNotFoundError(f"Expected study PDF at {pdf_path}")

    documents = PyPDFLoader(str(pdf_path)).load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    # Start fresh so re-running (or switching PDFs) replaces chunks instead of duplicating them.
    Chroma(
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    ).delete_collection()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    )

    print(f"Loaded {len(documents)} pages from {pdf_path.name}")
    print(f"Stored {len(chunks)} chunks in {CHROMA_DIR}")

    preview = vectorstore.similarity_search("What is Metro Ethernet?", k=1)
    if preview:
        print("\nSample retrieved chunk:\n")
        print(preview[0].page_content[:500])


if __name__ == "__main__":
    ingest(Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_PATH)
