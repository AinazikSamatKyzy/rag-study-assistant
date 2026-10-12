"""Answer a question from the notes: retrieve top chunks, then let a local LLM write the answer."""

import os
import sys

import ollama
from langchain_ollama import ChatOllama

from query_notes import DEFAULT_QUESTION, TOP_K, load_vectorstore

# Local model served by Ollama. Download it once with: ollama pull llama3
# Override without editing code: set OLLAMA_MODEL=gemma3:4b
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "llama3")


def pick_model() -> str:
    """Use MODEL_NAME if Ollama has it, otherwise fall back to any installed model."""
    installed = [m.model for m in ollama.list().models]
    if not installed:
        raise RuntimeError(f"No Ollama models installed. Run: ollama pull {MODEL_NAME}")
    for name in installed:
        if name == MODEL_NAME or name == f"{MODEL_NAME}:latest":
            return name
    return installed[0]

PROMPT = """You are a study assistant. Answer the question using ONLY the notes below.
If the notes do not contain the answer, say "The notes don't cover this."
Keep the answer short and clear.

Notes:
{context}

Question: {question}
Answer:"""


def answer_question(question: str) -> dict:
    """Return the answer plus the chunks it was based on."""
    vectorstore = load_vectorstore()
    results = vectorstore.similarity_search(question, k=TOP_K)
    if not results:
        return {"answer": "No matching chunks found.", "sources": []}

    context = "\n\n---\n\n".join(doc.page_content.strip() for doc in results)
    llm = ChatOllama(model=pick_model(), temperature=0)
    answer = llm.invoke(PROMPT.format(context=context, question=question))

    # PyPDFLoader pages are 0-based; show the slide number a reader would see.
    sources = [
        {
            "page": doc.metadata["page"] + 1 if "page" in doc.metadata else None,
            "text": doc.page_content.strip(),
        }
        for doc in results
    ]
    return {"answer": answer.content.strip(), "sources": sources}


def ask_notes(question: str) -> None:
    result = answer_question(question)
    print(f"Question: {question}\n")
    print(f"Answer:\n{result['answer']}\n")

    pages = sorted({s["page"] for s in result["sources"] if s["page"] is not None})
    if pages:
        print(f"Sources: pages {', '.join(map(str, pages))}")


if __name__ == "__main__":
    # Windows consoles may default to a legacy codepage that can't print PDF symbols.
    sys.stdout.reconfigure(encoding="utf-8")
    # Usage: python ask_notes.py "your question here"
    question = " ".join(sys.argv[1:]).strip() or DEFAULT_QUESTION
    ask_notes(question)
