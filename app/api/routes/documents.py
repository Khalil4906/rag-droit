from fastapi import APIRouter, HTTPException  

from app.schemas.chat import (
    DocumentsResponse,       
    DocumentInfo,            
    DeleteDocumentResponse,  
)
from app.rag.dense_retriever import (
    list_documents,   
    delete_document,  
)
from app.rag.sparse_retriever import (
    delete_document_sparse,   
)


router = APIRouter()  


@router.get("/documents", response_model=DocumentsResponse)
async def get_documents() -> DocumentsResponse:
    try:
        docs_raw = await list_documents()

    except Exception as e:
        raise HTTPException(
            status_code=503,  
            detail=f"Base de données indisponible : {str(e)}",
        )

    documents = [
        DocumentInfo(
            doc_id=d["doc_id"],          
            source=d["source"],          
            chunk_count=d["chunk_count"],  
            page_count=d["page_count"],  
            indexed_at=d["indexed_at"],  
        )
        for d in docs_raw  
    ]

    return DocumentsResponse(
        documents=documents,      
        total=len(documents),     
    )


@router.delete(
    "/documents/{doc_id}",
    response_model=DeleteDocumentResponse,
)
async def delete_doc(doc_id: str) -> DeleteDocumentResponse:
    try:
        docs = await list_documents()
        doc_ids_existing = {d["doc_id"] for d in docs}

        if doc_id not in doc_ids_existing:
            raise HTTPException(
                status_code=404,  
                detail=f"Document introuvable : {doc_id}",
            )

    except HTTPException:
        raise  # relaie les 404 sans les attraper

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Base de données indisponible : {str(e)}",
        )

    try:
        n_dense = await delete_document(doc_id)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur suppression pgvector : {str(e)}",
        )
        
    bm25_warning = None 

    try:
        n_sparse = delete_document_sparse(doc_id)

    except Exception as e:
        n_sparse = 0
        bm25_warning = (
            f"Document supprimé de pgvector mais "
            f"erreur BM25 : {str(e)}. "
            f"Relance scripts/init_db.py pour réparer."
        )

    return DeleteDocumentResponse(
        doc_id=doc_id,                    
        chunks_deleted_dense=n_dense,     
        chunks_deleted_sparse=n_sparse,   
        status=(
            "ok" if not bm25_warning      
            else f"warning: {bm25_warning}"  
        ),
    )