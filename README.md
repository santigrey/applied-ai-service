# Applied AI Service

A minimal, production-oriented applied AI service demonstrating LLM-backed chat,
persistent memory, and retrieval using FastAPI and OpenAI.

## Table of Contents

- [Installation](#installation)
- [Quickstart (local)](#quickstart-local)
- [Quickstart (Docker)](#quickstart-docker)
- [API examples](#api-examples)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. Clone the repo:
```bash
git clone https://github.com/santigrey/applied-ai-service.git
cd applied-ai-service
```

2. Create a virtualenv and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Copy environment template and provide secrets:
```bash
cp .env.example .env
# For local (non-Docker) runs, you may also export directly:
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

## Quickstart (local)

Run the FastAPI app with uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open http://localhost:8000/docs for interactive API docs.

## Quickstart (Docker)

Build and run with Docker Compose:
```bash
cp .env.example .env
docker compose up --build
```

Stop and remove:
```bash
docker compose down
```

## API examples

Health:
```bash
curl -s http://localhost:8000/health
# -> { "status": "ok" }
```

Stats:
```bash
curl http://localhost:8000/stats
```

Ingest (example):
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"name":"doc1","text":"Your document text here"}'
```

Chat (example):
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"user-123","message":"Hello, assist me with X."}'
```

## Configuration

- `OPENAI_API_KEY` — API key for OpenAI
- `.env` — local configuration copied from `.env.example`

The service persists conversation state in SQLite and stores embeddings for retrieval.

## Contributing

Contributions are welcome. Open an issue or PR. Keep changes small, include tests where applicable, and follow explicit prompt handling and minimal-abstraction principles.

## License

MIT
