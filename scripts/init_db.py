import asyncio  
import os  
import sys  
from pathlib import Path  

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  
load_dotenv()  


SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

-- table des chunks vectorisés — utilisée par pgvector
CREATE TABLE IF NOT EXISTS embeddings (
    id          SERIAL PRIMARY KEY,
    doc_id      TEXT NOT NULL,
    source      TEXT NOT NULL,
    page        INTEGER,
    chunk_index INTEGER,
    content     TEXT NOT NULL,
    embedding   vector(384),
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- index HNSW pour la recherche cosine — meilleur compromis
-- vitesse/précision pour les petites collections
CREATE INDEX IF NOT EXISTS embeddings_hnsw_idx
    ON embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- index sur doc_id pour les DELETE rapides par document
CREATE INDEX IF NOT EXISTS embeddings_doc_id_idx
    ON embeddings (doc_id);

-- table des messages de conversation — historique persisté
CREATE TABLE IF NOT EXISTS conversations (
    id          SERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL,   -- identifiant unique de session Streamlit
    role        TEXT NOT NULL,   -- "human" ou "assistant"
    content     TEXT NOT NULL,   -- contenu du message
    intent      TEXT,            -- intent détecté : chat/rag/summarize/fiche
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- index sur session_id + created_at pour charger l'historique
-- d'une session dans l'ordre chronologique rapidement
CREATE INDEX IF NOT EXISTS conversations_session_idx
    ON conversations (session_id, created_at);
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
        print("OK — tables embeddings + conversations créées.")
        print("OK — index HNSW + doc_id + session créés.")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init())