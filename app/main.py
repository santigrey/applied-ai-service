from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import OpenAI

from app.db import (
    init_db,
    load_messages,
    save_message,
    create_document,
    add_chunk,
    search_chunks,
)

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


class IngestRequest(BaseModel):
    name: str
    text: str


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


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

    return {"status": "ok", "document_id": doc_id, "chunks_added": len(chunks)}


@app.post("/chat")
def chat(req: ChatRequest):
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
                "content": "Use the following retrieved context when helpful:\n\n"
                + context_block,
            },
        )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    assistant_text = completion.choices[0].message.content or ""

    save_message(req.conversation_id, "user", req.message)
    save_message(req.conversation_id, "assistant", assistant_text)

    return {"response": assistant_text}