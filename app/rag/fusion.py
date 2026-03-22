import re
from typing import Any


_LEGAL_REF_PATTERN = re.compile(
    r'\barticle\b'
    r'|art\.?\s+\w+'
    r'|alin[ée]a\.?\s+\d+'
    r'|\b(\d{3,})\b'
    r'|[lr]\.\s*\d+[-\d]*'
    r'|\b[lr]\d+[-\d]*\b',
    re.IGNORECASE,
)


def is_legal_reference(query: str) -> bool:
    return bool(_LEGAL_REF_PATTERN.search(query))


def route_search(query: str) -> str:
    if is_legal_reference(query):
        return "sparse"
    return "hybrid"


def rrf_fusion(
    dense_results: list[dict[str, Any]],
    sparse_results: list[dict[str, Any]],
    k: int = 60,
) -> list[dict[str, Any]]:
    scores: dict[tuple[str, int], float] = {}
    result_map: dict[tuple[str, int], dict[str, Any]] = {}

    for rank, result in enumerate(dense_results):
        key = (result["doc_id"], result["chunk_index"])
        rrf_score = 1.0 / (k + rank + 1)
        scores[key] = scores.get(key, 0.0) + rrf_score
        result_map[key] = result

    for rank, result in enumerate(sparse_results):
        key = (result["doc_id"], result["chunk_index"])
        rrf_score = 1.0 / (k + rank + 1)
        scores[key] = scores.get(key, 0.0) + rrf_score
        if key not in result_map:
            result_map[key] = result

    sorted_keys = sorted(
        scores.keys(),
        key=lambda k: scores[k],
        reverse=True,
    )

    fused = []
    for key in sorted_keys:
        result = result_map[key].copy()
        result["score_rrf"] = round(scores[key], 6)
        result["score_dense"] = (
            result.get("score")
            if result.get("retriever") == "dense"
            else None
        )
        result["score_sparse"] = (
            result.get("score")
            if result.get("retriever") == "sparse"
            else None
        )
        result["score"] = result["score_rrf"]
        fused.append(result)

    return fused


def log_fusion_stats(
    dense_results: list[dict[str, Any]],
    sparse_results: list[dict[str, Any]],
    fused_results: list[dict[str, Any]],
) -> None:
    dense_keys = {
        (r["doc_id"], r["chunk_index"]) for r in dense_results
    }
    sparse_keys = {
        (r["doc_id"], r["chunk_index"]) for r in sparse_results
    }

    both = dense_keys & sparse_keys
    only_dense = dense_keys - sparse_keys
    only_sparse = sparse_keys - dense_keys

    print(f"\n── Fusion stats ──────────────────────────")
    print(f"  Dense         : {len(dense_results)} chunks")
    print(f"  Sparse        : {len(sparse_results)} chunks")
    print(f"  Dans les deux : {len(both)} chunks")
    print(f"  Dense seul    : {len(only_dense)} chunks")
    print(f"  Sparse seul   : {len(only_sparse)} chunks")
    print(f"  Apres fusion  : {len(fused_results)} chunks uniques")
    print(f"──────────────────────────────────────────\n")

    for i, r in enumerate(fused_results[:5], 1):
        retriever_tag = r.get("retriever", "both")
        print(
            f"  [{i}] {r['source']} p.{r['page']}"
            f" — rrf={r['score_rrf']:.6f}"
            f" — via {retriever_tag}"
        )