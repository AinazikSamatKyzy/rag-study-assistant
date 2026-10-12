FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FASTEMBED_CACHE_PATH=/opt/fastembed \
    CHROMA_DIR=/data/chroma_db \
    NOTES_PDF=/app/samples/kubernetes_notes.pdf \
    OLLAMA_HOST=http://ollama:11434

WORKDIR /app

# Dependencies first: this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Bake the embedding model into the image so pods start without downloading it.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"

COPY *.py ./
COPY static/ static/
COPY samples/kubernetes_notes.pdf samples/

RUN useradd --create-home appuser && mkdir -p /data && chown appuser /data /opt/fastembed -R
USER appuser

EXPOSE 5000
# Build the vector database from NOTES_PDF, then serve. One worker keeps a single
# copy of the embedding model in memory; threads handle concurrent requests.
# The long timeout covers slow first answers while a CPU-only LLM loads.
CMD ["sh", "-c", "python ingest_notes.py && exec gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 4 --timeout 600 app:app"]
