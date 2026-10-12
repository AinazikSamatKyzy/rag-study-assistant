"""Web UI for the study assistant. Run: python app.py, then open http://127.0.0.1:5000"""

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from ask_notes import MODEL_NAME, answer_question, pick_model
from query_notes import load_vectorstore

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = Flask(__name__)


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/api/status")
def status():
    try:
        chunks = load_vectorstore()._collection.count()
        return jsonify({"ok": True, "model": pick_model(), "chunks": chunks})
    except Exception as exc:
        return jsonify({"ok": False, "model": MODEL_NAME, "error": str(exc)})


@app.post("/api/ask")
def ask():
    question = (request.get_json(silent=True) or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "Please type a question."}), 400
    try:
        return jsonify(answer_question(question))
    except Exception as exc:
        message = str(exc)
        if "not found" in message and "model" in message:
            message = f"Ollama model '{MODEL_NAME}' is not installed. Run: ollama pull {MODEL_NAME}"
        elif "connect" in message.lower():
            message = "Can't reach Ollama. Make sure the Ollama app is running."
        return jsonify({"error": message}), 500


@app.get("/healthz")
def healthz():
    """Liveness check for Kubernetes: the web process is up (does not touch Ollama)."""
    return jsonify({"ok": True})


if __name__ == "__main__":
    # In a container set HOST=0.0.0.0 so the port is reachable from outside.
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=5000, debug=False)
