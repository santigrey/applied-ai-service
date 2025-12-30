from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
import os
import time
import uuid
import json
import logging

from openai import OpenAI
from openai import OpenAIError, RateLimitError, AuthenticationError, BadRequestError

from app.db import (
    init_db,
    load_messages,
    save_message,
    create_document,
    add_chunk,
    search_chunks,
    get_counts,
)

# -------- Logging (stdlib only) --------
logger = logging.getLogger("applied_ai_service")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setLevel(logging.INFO)
logger.addHandler(_handler)


def log_event(event: str, **fields) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False))


# -------- App --------
app = FastAPI()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    # Fail fast: better than crashing later in a request
    raise RuntimeError("OPENAI_API_KEY is not set in the environment.")

client = OpenAI(api_key=API_KEY)


# -------- Models --------
class ChatRequest(BaseModel):
    conversation_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=4000)


class IngestRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    text: str = Field(..., min_length=1, max_length=200000)


# -------- Startup --------
@app.on_event("startup")
def startup():
    init_db()
    log_event("startup", status="ok")


# -------- Middleware (request_id + timing) --------
@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.time()

    try:
        response = await call_next(request)
    except Exception as e:
        # Ensure we log unexpected crashes with a request_id
        elapsed_ms = int((time.time() - start) * 1000)
        log_event(
            "request_error",
            request_id=request_id,
            method=request.method,
            path=str(request.url.path),
            elapsed_ms=elapsed_ms,
            error_type=type(e).__name__,
            error=str(e),
        )
        raise

    elapsed_ms = int((time.time() - start) * 1000)
    log_event(
        "request_complete",
        request_id=request_id,
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        elapsed_ms=elapsed_ms,
    )
    response.headers["x-request-id"] = request_id
    return response


# -------- Exception handlers (guardrails) --------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = request.headers.get("x-request-id")
    log_event(
        "validation_error",
        request_id=request_id,
        path=str(request.url.path),
        errors=exc.errors(),
    )
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "details": exc.errors()},
    )


@app.exception_handler(AuthenticationError)
async def openai_auth_handler(request: Request, exc: AuthenticationError):
    request_id = request.headers.get("x-request-id")
    log_event("openai_auth_error", request_id=request_id, error=str(exc))
    return JSONResponse(
        status_code=401,
        content={"error": "openai_auth_error", "message": "Invalid or missing OpenAI credentials."},
    )


@app.exception_handler(RateLimitError)
async def openai_rate_limit_handler(request: Request, exc: RateLimitError):
    request_id = request.headers.get("x-request-id")
    log_event("openai_rate_limit", request_id=request_id, error=str(exc))
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limited", "message": "Upstream rate limit or quota exceeded."},
    )


@app.exception_handler(BadRequestError)
async def openai_bad_request_handler(request: Request, exc: BadRequestError):
    request_id = request.headers.get("x-request-id")
    log_event("openai_bad_request", request_id=request_id, error=str(exc))
    return JSONResponse(
        status_code=400,
        content={"error": "openai_bad_request", "message": "Bad request sent to upstream LLM API."},
    )


@app.exception_handler(OpenAIError)
async def openai_generic_handler(request: Request, exc: OpenAIError):
    request_id = request.headers.get("x-request-id")
    log_event("openai_error", request_id=request_id, error=str(exc))
    return JSONResponse(
        status_code=502,
        content={"error": "openai_error", "message": "Upstream LLM API error."},
    )


# -------- Endpoints --------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def stats():
    return {"status": "ok", **get_counts()}


@app.post("/ingest")
def ingest(req: IngestRequest):
    doc_id = create_document(req.name)

    text = req.text.strip()
    chunk_size = 800
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    for chunk in chunks:
        emb = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk,
        ).data[0].embedding
        add_chunk(doc_id, chunk, emb)

    log_event("ingest_complete", document_id=doc_id, chunks_added=len(chunks), name=req.name)
    return {"status": "ok", "document_id": doc_id, "chunks_added": len(chunks)}


@app.post("/chat")
def chat(req: ChatRequest):
    # Load conversation history
    history = load_messages(req.conversation_id, limit=20)
    messages = [{"role": role, "content": content} for role, content in history]
    messages.append({"role": "user", "content": req.message})

    # Retrieval: embed query + fetch top chunks
    query_emb = client.embeddings.create(
        model="text-embedding-3-small",
        input=req.message,
    ).data[0].embedding

    retrieved = search_chunks(query_emb, top_k=4)

    if retrieved:
        context_block = "\n\n---\n\n".join(retrieved)
        messages.insert(
            0,
            {
                "role": "system",
                "content": "Use the following retrieved context when helpful:\n\n" + context_block,
            },
        )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    assistant_text = completion.choices[0].message.content or ""

    save_message(req.conversation_id, "user", req.message)
    save_message(req.conversation_id, "assistant", assistant_text)

    log_event(
        "chat_complete",
        conversation_id=req.conversation_id,
        retrieved_chunks=len(retrieved),
        user_chars=len(req.message),
        assistant_chars=len(assistant_text),
    )

    return {"response": assistant_text}