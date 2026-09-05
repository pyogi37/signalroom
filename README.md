# SignalRoom

SignalRoom is a synthetic, portfolio-safe **voice-first AI solutioning engineer**. It turns a messy
customer discovery conversation into evidence-backed requirements, open questions, risks, and a
reviewable solution brief.

This repository is an independent build. Its demo organizations, people, documents, tools, and data
are fictional.

## V1

- Discovery workspace with a transcript-like evidence feed
- Explicit agent stages: discover, structure, retrieve, design, critique, approve
- Requirements with source evidence and confidence
- Human approval boundary before finalization
- Synthetic tool results and knowledge documents
- Paste-your-own synthetic transcript analysis
- Embedded Qdrant vector retrieval with deterministic local embeddings
- Persistent SQLite solution rooms and audit events
- Optional OpenAI structured-output and audio-transcription adapters
- Read-only MCP server for knowledge, room, and evaluation tools
- DOCX solution-brief export
- FastAPI backend with a LangGraph workflow
- React/Vite frontend designed as a solutioning workbench

## Run locally

Backend:

```powershell
cd apps/api
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\uvicorn signalroom.main:app --reload --port 8000
```

Frontend:

```powershell
cd apps/web
npm install
npm run dev
```

Open `http://localhost:5173`. Click **Analyze new discovery** to run a synthetic transcript through
the extraction and retrieval pipeline. The frontend falls back to embedded synthetic demo data if the API is
not running, so the portfolio walkthrough remains usable.

### Optional live model and voice

Copy `.env.example` to `.env`, set `OPENAI_API_KEY`, and change `SIGNALROOM_LLM_PROVIDER` to
`openai`. Without a key, SignalRoom stays in deterministic local mode and clearly labels itself as
such. Secrets are never required for the reproducible demo and must not be committed.

### MCP server

With the API running:

```powershell
cd apps/api
.venv\Scripts\python -m signalroom.mcp_server
```

The MCP surface is intentionally read-only. Approval remains a human action in the product UI.

### Evaluations

```powershell
cd apps/api
.venv\Scripts\python evals/run.py
```

The checked-in synthetic fixtures measure requirement precision/recall and grounding. They run in
deterministic mode in CI; a live-model evaluation can use the same labeled cases.

## Architecture

See [docs/architecture.md](docs/architecture.md) and [docs/evaluation.md](docs/evaluation.md).
