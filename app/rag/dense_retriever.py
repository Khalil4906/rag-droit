from typing import Any

import google.genai as genai
from google.genai import types
from langchain_core.documents import Document

from app.core.config import get_settings
from app.db.session import get_pool


def _get_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(api_key=settings.google_api_key)


async def _embed(
    texts: list[str],
    is_query: bool = False,
) -> list[list[float]]:
    task_type = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    client = _get_client()

    batch_size = 100
    all_vectors = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        result = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=768,
            ),
        )
        all_vectors.extend([e.values for e in result.embeddings])

    return all_vectors

def _vector_to_str(vector: list[float]) -> str:
    return "[" + ",".join(map(str, vector)) + "]"


async def index_documents(chunks: list[Document]) -> int:
    if not chunks:
        return 0

    texts = [chunk.page_content for chunk in chunks]
    vectors = await _embed(texts, is_query=False)

    records = [
        (
            chunk.metadata["doc_id"],
            chunk.metadata["source"],
            chunk.metadata.get("page", 0),
            chunk.metadata["chunk_index"],
            chunk.page_content,
            _vector_to_str(vectors[i]),
        )
        for i, chunk in enumerate(chunks)
    ]

    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO embeddings
                    (doc_id, source, page, chunk_index,
                     content, embedding)
                VALUES
                    ($1, $2, $3, $4, $5, $6::vector)
                ON CONFLICT DO NOTHING
                """,
                records,
            )

    return len(records)


async def search_dense(
    query: str,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    settings = get_settings()
    k = top_k or settings.dense_top_k

    query_vector = (await _embed([query], is_query=True))[0]

    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                doc_id, source, page, chunk_index, content,
                1 - (embedding <=> $1::vector) AS score
            FROM embeddings
            ORDER BY embedding <=> $1::vector
            LIMIT $2
            """,
            _vector_to_str(query_vector),
            k,
        )

    return [
        {
            "doc_id": row["doc_id"],
            "source": row["source"],
            "page": row["page"],
            "chunk_index": row["chunk_index"],
            "content": row["content"],
            "score": float(row["score"]),
            "retriever": "dense",
        }
        for row in rows
    ]


async def delete_document(doc_id: str) -> int:
    pool = get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM embeddings WHERE doc_id = $1",
            doc_id,
        )
        return int(result.split()[-1])


async def list_documents() -> list[dict[str, Any]]:
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                doc_id, source,
                COUNT(*) AS chunk_count,
                MAX(page) AS page_count,
                MIN(created_at) AS indexed_at
            FROM embeddings
            GROUP BY doc_id, source
            ORDER BY indexed_at DESC
            """
        )

    return [
        {
            "doc_id": row["doc_id"],
            "source": row["source"],
            "chunk_count": row["chunk_count"],
            "page_count": row["page_count"],
            "indexed_at": row["indexed_at"].isoformat(),
        }
        for row in rows
    ]