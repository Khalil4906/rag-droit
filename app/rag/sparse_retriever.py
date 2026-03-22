import json
import re
from typing import Any

from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

from app.db.session import get_pool


_bm25_cache: BM25Okapi | None = None
_metadata_cache: list[dict[str, Any]] | None = None
_cache_dirty: bool = True


def _invalidate_cache() -> None:
    global _bm25_cache, _metadata_cache, _cache_dirty
    _bm25_cache = None
    _metadata_cache = None
    _cache_dirty = True


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = text.replace('\u2019', ' ')
    text = text.replace('\u2018', ' ')
    text = text.replace('\u0027', ' ')
    text = text.replace('`', ' ')

    text = re.sub(
        r'\b(article|art\.?|alinéa|al\.?)\s+'
        r'(\w+)'
        r'\s+(?:du\s+|de\s+|de\s+la\s+)?'
        r'code\s+'
        r'(\w+)',
        lambda m: m.group(1) + "_" + m.group(2) + "_" + m.group(3),
        text,
    )

    text = re.sub(
        r'\b(article|art\.?|alinéa|al\.?)\s+(\w+)\b',
        lambda m: m.group(1) + "_" + m.group(2),
        text,
    )

    text = re.sub(
        r'\b([lr])\.\s*(\d+[-\d]*)\b',
        lambda m: m.group(1) + "_" + m.group(2),
        text,
    )

    text = re.sub(
        r'\b([lr])(\d+[-\d]*)\b',
        lambda m: m.group(1) + "_" + m.group(2),
        text,
    )

    text = re.sub(r'[^\w\s_-]', ' ', text)

    return text.split()


async def _load_from_db() -> tuple[BM25Okapi | None, list[dict[str, Any]]]:
    global _bm25_cache, _metadata_cache, _cache_dirty

    if not _cache_dirty and _bm25_cache is not None:
        return _bm25_cache, _metadata_cache

    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT doc_id, source, page, chunk_index, content, tokens
            FROM bm25_index
            ORDER BY id ASC
            """
        )

    if not rows:
        _bm25_cache = None
        _metadata_cache = []
        _cache_dirty = False
        return None, []

    corpus = []
    metadata = []

    for row in rows:
        tokens = json.loads(row["tokens"])
        corpus.append(tokens)
        metadata.append({
            "doc_id": row["doc_id"],
            "source": row["source"],
            "page": row["page"],
            "chunk_index": row["chunk_index"],
            "content": row["content"],
        })

    _bm25_cache = BM25Okapi(corpus)
    _metadata_cache = metadata
    _cache_dirty = False

    return _bm25_cache, _metadata_cache


async def index_documents_sparse(chunks: list[Document]) -> int:
    if not chunks:
        return 0

    pool = get_pool()

    async with pool.acquire() as conn:
        existing = await conn.fetchval(
            "SELECT COUNT(*) FROM bm25_index WHERE doc_id = $1",
            chunks[0].metadata["doc_id"],
        )

        if existing > 0:
            return 0

        records = [
            (
                chunk.metadata["doc_id"],
                chunk.metadata["source"],
                chunk.metadata.get("page", 0),
                chunk.metadata["chunk_index"],
                chunk.page_content,
                json.dumps(
                    _tokenize(chunk.page_content),
                    ensure_ascii=False,
                ),
            )
            for chunk in chunks
        ]

        async with conn.transaction():
            await conn.executemany(
                """
                INSERT INTO bm25_index
                    (doc_id, source, page, chunk_index, content, tokens)
                VALUES
                    ($1, $2, $3, $4, $5, $6)
                """,
                records,
            )

    _invalidate_cache()
    return len(records)


async def search_sparse(
    query: str,
    top_k: int = 20,
) -> list[dict[str, Any]]:
    bm25, metadata = await _load_from_db()

    if bm25 is None or not metadata:
        return []

    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)

    top_indices = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True,
    )[:top_k]

    return [
        {
            "doc_id": metadata[i]["doc_id"],
            "source": metadata[i]["source"],
            "page": metadata[i]["page"],
            "chunk_index": metadata[i]["chunk_index"],
            "content": metadata[i]["content"],
            "score": float(scores[i]),
            "retriever": "sparse",
        }
        for i in top_indices
        if scores[i] > 0
    ]


async def delete_document_sparse(doc_id: str) -> int:
    pool = get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM bm25_index WHERE doc_id = $1",
            doc_id,
        )
        deleted = int(result.split()[-1])

    _invalidate_cache()
    return deleted


async def list_documents_sparse() -> list[str]:
    pool = get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT DISTINCT doc_id FROM bm25_index"
        )

    return [row["doc_id"] for row in rows]