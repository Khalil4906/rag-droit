import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS embeddings (
    id          SERIAL PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    source      TEXT NOT NULL,
    page        INTEGER,
    chunk_index INTEGER,
    content     TEXT NOT NULL,
    embedding   vector(768),
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS embeddings_hnsw_idx
    ON embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS embeddings_doc_id_idx
    ON embeddings (doc_id);

CREATE TABLE IF NOT EXISTS conversations (
    id          SERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL,
    content     TEXT NOT NULL,
    intent      TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS conversations_session_idx
    ON conversations (session_id, created_at);

CREATE TABLE IF NOT EXISTS bm25_index (
    id          SERIAL PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    source      TEXT NOT NULL,
    page        INTEGER,
    chunk_index INTEGER,
    content     TEXT NOT NULL,
    tokens      TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS bm25_doc_id_idx
    ON bm25_index (doc_id);
"""


async def init() -> None:
    import asyncpg

    url = os.getenv("DATABASE_URL", "")

    if not url:
        print("ERREUR — DATABASE_URL manquante dans .env")
        sys.exit(1)

    url = url.replace("postgres://", "postgresql://")
    conn = await asyncpg.connect(url)

    try:
        await conn.execute(SQL)
        print("OK — toutes les tables et index créés.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init())