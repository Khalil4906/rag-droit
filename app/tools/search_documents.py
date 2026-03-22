from typing import Optional

from langchain.tools import tool 

from app.rag.dense_retriever import search_dense  
from app.rag.sparse_retriever import search_sparse 
from app.rag.fusion import route_search, rrf_fusion  


def _filter_by_doc(
    results: list[dict],
    doc_filter: Optional[str],
) -> list[dict]:
    if not doc_filter:
        return results

    doc_filter_lower = doc_filter.lower()
    return [
        r for r in results
        if doc_filter_lower in r["source"].lower()
    ]


def _format_results(results: list[dict]) -> str:

    if not results:
        return (
            "Aucun passage pertinent trouvé dans les documents. "
            "Reformule ta question ou vérifie que le document "
            "est bien indexé."
        )

    lines = []  

    for i, r in enumerate(results, 1):
        page_info = (
            f"p.{r['page']}"
            if r["page"] != 0  
            else "page inconnue"  
        )

        lines.append(
            f"[{i}] {r['source']} — {page_info}\n"
            f"    {r['content']}"

        )

    return "\n\n".join(lines)


@tool
async def search_documents(
    query: str,
    doc_filter: Optional[str] = None,
) -> str:
    """Recherche des documents juridiques
    pertinents par rapport à une requête."""
    strategy = route_search(query)

    if strategy == "sparse":
        results = search_sparse(query)

    else:
        dense_results = await search_dense(query)
        sparse_results = search_sparse(query)
        results = rrf_fusion(dense_results, sparse_results)
    results = _filter_by_doc(results, doc_filter)
    results = results[:6]

    return _format_results(results)