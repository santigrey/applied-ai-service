import sqlite3
import json
import math
from pathlib import Path
from typing import List, Tuple

DB_PATH = Path(__file__).resolve().parent / "data.sqlite3"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        # Conversation memory
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_convo ON messages(conversation_id, id)"
        )

        # Retrieval tables
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding_json TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(document_id, id)")


def save_message(conversation_id: str, role: str, content: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
            (conversation_id, role, content),
        )


def load_messages(conversation_id: str, limit: int = 20) -> List[Tuple[str, str]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (conversation_id, limit),
        ).fetchall()
    rows.reverse()
    return [(r[0], r[1]) for r in rows]


def create_document(name: str) -> int:
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO documents (name) VALUES (?)", (name,))
        return int(cur.lastrowid)


def add_chunk(document_id: int, content: str, embedding: List[float]) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO chunks (document_id, content, embedding_json) VALUES (?, ?, ?)",
            (document_id, content, json.dumps(embedding)),
        )


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    denom = math.sqrt(na) * math.sqrt(nb)
    return dot / denom if denom else 0.0


def search_chunks(query_embedding: List[float], top_k: int = 4) -> List[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT content, embedding_json FROM chunks").fetchall()

    scored: List[Tuple[float, str]] = []
    for content, emb_json in rows:
        emb = json.loads(emb_json)
        score = _cosine_similarity(query_embedding, emb)
        scored.append((score, content))

    scored.sort(key=lambda t: t[0], reverse=True)
    return [c for _, c in scored[:top_k]]


def get_counts() -> dict:
    with get_conn() as conn:
        messages = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        documents = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    return {"messages": int(messages), "documents": int(documents), "chunks": int(chunks)}