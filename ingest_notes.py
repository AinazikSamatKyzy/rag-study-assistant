"""Load Chap.3 Metro Ethernet notes, chunk them, and store in local Chroma."""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

PDF_PATH = Path(__file__).resolve().parent / "Chap3_Metro_Ethernet.pdf"
CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"
COLLECTION_NAME = "metro_ethernet_notes"


def ingest() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"Expected study PDF at {PDF_PATH}")

    documents = PyPDFLoader(str(PDF_PATH)).load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    embeddings = FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name=COLLECTION_NAME,
    )

    print(f"Loaded {len(documents)} pages from {PDF_PATH.name}")
    print(f"Stored {len(chunks)} chunks in {CHROMA_DIR}")

    preview = vectorstore.similarity_search("What is Metro Ethernet?", k=1)
    if preview:
        print("\nSample retrieved chunk:\n")
        print(preview[0].page_content[:500])


if __name__ == "__main__":
    ingest()
