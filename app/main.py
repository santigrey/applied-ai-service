from fastapi import FastAPI
from pydantic import BaseModel
import os
from openai import OpenAI

from app.db import init_db, load_messages, save_message

app = FastAPI()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatRequest(BaseModel):
    conversation_id: str
    message: str

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    history = load_messages(req.conversation_id, limit=20)

    messages = [{"role": role, "content": content} for role, content in history]
    messages.append({"role": "user", "content": req.message})

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    assistant_text = completion.choices[0].message.content or ""

    save_message(req.conversation_id, "user", req.message)
    save_message(req.conversation_id, "assistant", assistant_text)

    return {"response": assistant_text}