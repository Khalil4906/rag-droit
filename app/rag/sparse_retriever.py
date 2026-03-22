import json  
from pathlib import Path  
from typing import Any  

from rank_bm25 import BM25Okapi 
from langchain_core.documents import Document  

from app.core.config import get_settings  


import re


def _tokenize(text: str) -> list[str]:
    text = text.lower()

    # normalise toutes les formes d'apostrophes
    text = text.replace('\u2019', ' ')
    text = text.replace('\u2018', ' ')
    text = text.replace('\u0027', ' ')
    text = text.replace('`', ' ')

    # fusion article + numéro + code nommé
    # "article 372 du code civil" → "article_372_civil"
    text = re.sub(
        r'\b(article|art\.?|alinéa|al\.?)\s+'
        r'(\w+)'
        r'\s+(?:du\s+|de\s+|de\s+la\s+)?'
        r'code\s+'
        r'(\w+)',
        lambda m: (
            m.group(1) + "_"
            + m.group(2) + "_"
            + m.group(3)
        ),
        text,
    )

    # fusion article + numéro seul
    # "article 372" → "article_372"
    text = re.sub(
        r'\b(article|art\.?|alinéa|al\.?)\s+(\w+)\b',
        lambda m: m.group(1) + "_" + m.group(2),
        text,
    )

    # fusion références L./R. avec point
    # "L.111-1" → "l_111-1"
    text = re.sub(
        r'\b([lr])\.\s*(\d+[-\d]*)\b',
        lambda m: m.group(1) + "_" + m.group(2),
        text,
    )

    # fusion références L/R collées sans point
    # "L721-3" → "l_721-3"
    text = re.sub(
        r'\b([lr])(\d+[-\d]*)\b',
        lambda m: m.group(1) + "_" + m.group(2),
        text,
    )

    # supprime la ponctuation collée aux tokens
    # "(article_372" → "article_372"
    # "civil." → "civil"
    text = re.sub(r'[^\w\s_-]', ' ', text)

    return text.split()


def _load_index(
    index_path: str,
) -> tuple[BM25Okapi | None, list[dict[str, Any]]]:
    
    path = Path(index_path) 

    if not path.exists():  
        return None, []  

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)  

    corpus = data["corpus"]      
    metadata = data["metadata"] 

    if not corpus:  
        return None, []

    bm25 = BM25Okapi(corpus)  

    return bm25, metadata 


def _save_index(
    corpus: list[list[str]],
    metadata: list[dict[str, Any]],
    index_path: str,
) -> None:
    path = Path(index_path)
    path.parent.mkdir(parents=True, exist_ok=True)  

    data = {
        "corpus": corpus,      
        "metadata": metadata, 
    }

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def index_documents_sparse(chunks: list[Document]) -> int:
    # vérifie qu'il y a des chunks à indexer
    if not chunks:
        return 0

    settings = get_settings()

    # charge l'index existant ou démarre avec des listes vides
    _, existing_metadata = _load_index(settings.bm25_index_path)

    # récupère les doc_id déjà présents dans l'index
    # un set pour une recherche O(1) — plus rapide qu'une liste
    existing_doc_ids = {
        m["doc_id"] for m in existing_metadata
    }

    # vérifie si ce document est déjà indexé
    # tous les chunks d'un même fichier ont le même doc_id
    # donc on vérifie juste le premier chunk
    current_doc_id = chunks[0].metadata["doc_id"]

    if current_doc_id in existing_doc_ids:
        # doc_id déjà présent — on ne duplique pas
        # cohérent avec ON CONFLICT DO NOTHING dans pgvector
        return 0

    # corpus existant reconstruit depuis les métadonnées
    existing_corpus = [
        _tokenize(m["content"])
        for m in existing_metadata
    ]

    # tokenise les nouveaux chunks
    new_corpus = [
        _tokenize(chunk.page_content)
        for chunk in chunks
    ]

    # prépare les métadonnées des nouveaux chunks
    new_metadata = [
        {
            "doc_id": chunk.metadata["doc_id"],
            "source": chunk.metadata["source"],
            "page": chunk.metadata.get("page", 0),
            "chunk_index": chunk.metadata["chunk_index"],
            "content": chunk.page_content,
        }
        for chunk in chunks
    ]

    # fusionne existant + nouveaux
    full_corpus = existing_corpus + new_corpus
    full_metadata = existing_metadata + new_metadata

    # persiste l'index complet mis à jour
    _save_index(full_corpus, full_metadata, settings.bm25_index_path)

    return len(new_corpus)  # nombre de chunks ajoutés 


def search_sparse(
    query: str,
    top_k: int | None = None,
) -> list[dict[str, Any]]:

    settings = get_settings() 
    k = top_k or settings.sparse_top_k  

    bm25, metadata = _load_index(
        settings.bm25_index_path
    )  

    if bm25 is None or not metadata:  
        return []  

    query_tokens = _tokenize(query)  

    scores = bm25.get_scores(query_tokens)  

    top_indices = sorted(
        range(len(scores)),   
        key=lambda i: scores[i],  
        reverse=True,
    )[:k]  

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
    ]


def delete_document_sparse(doc_id: str) -> int:

    settings = get_settings()  

    _, metadata = _load_index(
        settings.bm25_index_path
    )  

    if not metadata:  
        return 0

    kept_metadata = [
        m for m in metadata
        if m["doc_id"] != doc_id  
    ]

    deleted_count = len(metadata) - len(kept_metadata)  

    if deleted_count == 0:  
        return 0

    kept_corpus = [
        _tokenize(m["content"])  
        for m in kept_metadata
    ]

    _save_index(kept_corpus, kept_metadata, settings.bm25_index_path)

    return deleted_count  


def list_documents_sparse() -> list[str]:
    settings = get_settings()  
    _, metadata = _load_index(settings.bm25_index_path)  

    return list({m["doc_id"] for m in metadata}) 