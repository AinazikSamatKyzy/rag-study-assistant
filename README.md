# RAG Study Assistant

Ask questions about your lecture slides and get answers drawn only from them, with the slide numbers each answer came from. Everything runs locally: no API keys, and your notes never leave your machine.

Built with LangChain, Chroma, FastEmbed (`BAAI/bge-small-en-v1.5`), Ollama (`llama3`) and Flask. Packaged with Docker, deployable to Kubernetes, and every push is checked by a CI pipeline that blocks releases when retrieval quality drops.

[![CI](https://github.com/AinazikSamatKyzy/rag-study-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/AinazikSamatKyzy/rag-study-assistant/actions/workflows/ci.yml)

![Chat UI answering a question with its source slides, and refusing a question the notes don't cover](media/1-app-answer.png)

## How it works

![Architecture: ingestion and answering pipeline](media/2-architecture.png)

```
Ingestion (once)     PDF -> pages -> chunks (1000 chars, 200 overlap) -> embeddings -> Chroma
Answering            question -> embedding -> top 3 chunks -> grounded prompt -> local LLM -> answer + slides
```

The prompt tells the model to answer using only the retrieved notes, and to reply "The notes don't cover this." when they don't contain the answer.

| File | Purpose |
|---|---|
| `ingest_notes.py` | Loads the PDF, splits it into chunks, embeds them, and saves them to `chroma_db/` |
| `query_notes.py` | Retrieval only: prints the chunks that match a question (useful for debugging) |
| `ask_notes.py` | Full RAG: retrieves chunks and has the local LLM write an answer |
| `eval_retrieval.py` | Retrieval test: questions with known answer pages (`eval/*.json`), reports the hit rate; `--min-hit-rate` makes it fail for CI |
| `samples/kubernetes_notes.pdf` | Bundled original study notes (14 pages) so the project runs out of the box; regenerate with `samples/make_sample_pdf.py` |
| `Dockerfile`, `docker-compose.yml` | Container image and a local stack with Ollama |
| `k8s/` | Kubernetes manifests: app Deployment + Service + HPA, Ollama with a PersistentVolume, model-pull Job |
| `.github/workflows/ci.yml` | CI: retrieval quality gate, image build, deploy to a kind cluster, smoke test, push to GHCR |
| `app.py` | Flask web server: `GET /`, `GET /api/status`, `POST /api/ask` |
| `static/index.html` | Chat interface |

## Setup

1. Install [Ollama](https://ollama.com) and download the model:
   ```
   ollama pull llama3
   ```
2. Create a virtual environment and install dependencies:
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Add your own lecture slides as a PDF. Course slides are usually copyrighted, so they are not included in this repo and `*.pdf` is git-ignored.
4. Build the notes database (once, or whenever the PDF changes):
   ```
   python ingest_notes.py path\to\your_slides.pdf
   ```
   With no argument it uses the bundled `samples/kubernetes_notes.pdf`, which the web UI's example questions and the default eval cases are written for. For your own notes, add an eval file like `eval/metro_ethernet.json` (written for a Computer Networks chapter on Metro Ethernet).

## Usage

**Web app**
```
python app.py
```
Then open http://127.0.0.1:5000. The first answer can take a few minutes on CPU while the model loads.

**Command line**
```
python ask_notes.py "What is Metro Ethernet?"
python query_notes.py "What is Metro Ethernet?"
```

**Evaluate retrieval** (a few seconds, no LLM needed)
```
python eval_retrieval.py                                  # bundled notes
python eval_retrieval.py eval/metro_ethernet.json --min-hit-rate 0.85
```
Current results (correct page in the top 3): bundled Kubernetes notes 16/16 (100%), Metro Ethernet lecture slides 12/13 (92%).

![Retrieval evaluation output](media/3-retrieval-eval.png)

To use a different Ollama model, set `OLLAMA_MODEL` (for example `gemma3:4b`). If the chosen model isn't installed, the app falls back to any installed model.

## Docker

```
docker compose up --build
```
Then open http://localhost:5000. The first start downloads the LLM (`gemma3:4b`, about 3 GB) into a volume. The image builds the vector database from `NOTES_PDF` at startup, runs as a non-root user, and includes the embedding model so it starts without downloads.

## Kubernetes

```
kubectl apply -f k8s/namespace.yaml -f k8s/ollama.yaml -f k8s/app.yaml
```
The app is exposed on NodePort 30500. Two stateless replicas (each builds its own small index at startup) with startup, liveness and readiness probes, memory limits, rolling updates with zero unavailable pods, and an HPA scaling 2 to 5 replicas on CPU (needs metrics-server). Ollama keeps models on a PersistentVolumeClaim; a Job pulls the model once.

## CI/CD

On every push and pull request, GitHub Actions:
1. Builds the vector database and runs the retrieval evaluation. Below 85% the pipeline fails, so a change that hurts answer quality cannot ship.
2. Builds the Docker image and deploys it to a throwaway Kubernetes cluster (kind), waits for the rollout, and smoke-tests the running service.
3. On `main`, pushes the image to GitHub Container Registry (`ghcr.io/ainaziksamatkyzy/rag-study-assistant`).

## Limitations and next steps

- Only text is read from the slides; diagrams are ignored.
- Each question is independent (no chat memory).
- Slides that are mostly diagrams (like slide 19) produce near-empty chunks that still get retrieved and crowd out useful ones.
- Ideas to add: streaming answers, hybrid keyword + vector search, filtering out near-empty chunks, and PDF upload.
