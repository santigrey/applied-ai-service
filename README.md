# Applied AI Service

A minimal, production-oriented **Applied AI service** built with FastAPI and OpenAI.
This project demonstrates end-to-end integration of an LLM-backed API, focusing on correctness, clarity, and real-world engineering practices rather than demos or toy abstractions.

---

## Overview

This service exposes a simple HTTP API that:

* Accepts user input via a REST endpoint
* Calls a large language model (LLM) using the OpenAI API
* Returns a structured JSON response

The project is intentionally scoped to highlight **applied AI fundamentals**:

* Clean service boundaries
* Explicit dependency management
* Environment-based secret handling
* Verifiable runtime behavior

More advanced capabilities (memory, retrieval, tools, evaluation) are layered incrementally in later stages.

---

## Current Features

* FastAPI-based web service
* Health check endpoint for runtime verification
* `/chat` endpoint backed by a real LLM
* OpenAI API integration via environment variables
* Local development using Python virtual environments
* Clean, incremental Git history

---

## API Endpoints

### `GET /health`

Health check endpoint.

**Response**

```json
{ "status": "ok" }
```

---

### `POST /chat`

Send a single-turn message to the LLM.

**Request**

```json
{
  "message": "Say hello in one sentence"
}
```

**Response**

```json
{
  "response": "Hello! How can I assist you today?"
}
```

---

## Project Structure

```
applied-ai-service/
├── app/
│   └── main.py        # FastAPI application and endpoints
├── .venv/             # Python virtual environment (local only)
├── requirements.txt   # Runtime dependencies
├── README.md
└── .gitignore
```

---

## Running Locally

### Prerequisites

* Python 3.10+
* An OpenAI API key with available quota

---

### Setup

```bash
cd applied-ai-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your API key:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

---

### Start the Service

```bash
uvicorn app.main:app --reload
```

The service will be available at:

```
http://127.0.0.1:8000
```

---

### Verify

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Say hello in one sentence"}'
```

---

## Design Notes

This project deliberately avoids heavy frameworks and abstractions in early stages.
The goal is to demonstrate **clear reasoning, system ownership, and correctness** before introducing additional complexity such as:

* Persistent memory
* Retrieval and embeddings
* Tool/function calling
* Evaluation and observability
* Deployment concerns

---

## Status

🚧 **In active development**

Next milestones include:

* Conversation memory with persistent storage
* Context retrieval
* Improved error handling and evaluation hooks

---

## License

MIT
