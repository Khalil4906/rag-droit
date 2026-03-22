from functools import lru_cache  
from typing import Any  

from langchain_core.documents import Document  
from sentence_transformers import SentenceTransformer  

from app.core.config import get_settings  
from app.db.session import get_pool  


@lru_cache(maxsize=1)  
def get_embedding_model() -> SentenceTransformer:
    settings = get_settings()  
    model = SentenceTransformer(
        settings.embedding_model,  
        device="cpu",  
    )
    return model 


def _embed(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model() 
    vectors = model.encode(
        texts,  
        normalize_embeddings=True, 
        show_progress_bar=False,
        batch_size=32, 
    )
    return vectors.tolist() 

def _vector_to_str(vector: list[float]) -> str:
    return "[" + ",".join(map(str, vector)) + "]" 

async def index_documents(chunks: list[Document]) -> int:
    if not chunks: 
        return 0

    texts = [chunk.page_content for chunk in chunks]

    vectors = _embed(texts)

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
                    (doc_id, source, page, chunk_index, content, embedding)
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

    query_vector = _embed([query])[0]  

    pool = get_pool()  
    async with pool.acquire() as conn: 
        rows = await conn.fetch(
            """
            SELECT
                doc_id,
                source,
                page,
                chunk_index,
                content,
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
        deleted = int(result.split()[-1])  

    return deleted 


async def list_documents() -> list[dict[str, Any]]:
    pool = get_pool()  
    async with pool.acquire() as conn: 
        rows = await conn.fetch(
            """
            SELECT
                doc_id,
                source,
                COUNT(*) AS chunk_count,       -- nombre de chunks indexés
                MAX(page) AS page_count,        -- nombre approximatif de pages
                MIN(created_at) AS indexed_at   -- date d'indexation
            FROM embeddings
            GROUP BY doc_id, source
            ORDER BY indexed_at DESC            -- plus récent en premier
            """,
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