import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.db.session import connect_db, disconnect_db
from app.rag.loader import load_file, SUPPORTED_EXTENSIONS
from app.rag.dense_retriever import index_documents, search_dense
from app.rag.sparse_retriever import (
    index_documents_sparse,
    search_sparse,
)
from app.rag.fusion import (
    rrf_fusion,
    log_fusion_stats,
    route_search,
)


def resolve_files(path_arg: str) -> list[Path]:
    path = Path(path_arg)

    if path.is_dir():
        files = [
            f for f in path.iterdir()
            if f.is_file()
            and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        if not files:
            print(f"Aucun fichier supporté dans : {path}")
            sys.exit(1)
        return files

    if path.is_file():
        return [path]

    print(f"Chemin invalide : {path}")
    sys.exit(1)


async def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage :\n"
            "  python scripts/test_fusion.py <fichier> \"<question>\"\n"
            "  python scripts/test_fusion.py data\\raw\\ \"<question>\""
        )
        sys.exit(1)

    path_arg = sys.argv[1]
    query = sys.argv[2]

    files = resolve_files(path_arg)

    await connect_db()

    try:
        print(f"Indexation de {len(files)} fichier(s) :")
        total_dense = 0
        total_sparse = 0

        for file in files:
            print(f"  → {file.name}")
            chunks = load_file(str(file))
            n_dense = await index_documents(chunks)
            n_sparse = index_documents_sparse(chunks)
            total_dense += n_dense
            total_sparse += n_sparse
            print(
                f"     dense={n_dense}"
                f" sparse={n_sparse} chunks"
            )

        print(
            f"\nOK — total dense={total_dense}"
            f" sparse={total_sparse} chunks."
        )

        # ── Routing ────────────────────────────────────────────────
        strategy = route_search(query)
        print(f"\nRecherche : \"{query}\"")
        print(f"Strategie : {strategy}")

        if strategy == "sparse":
            print("→ BM25 uniquement (mot 'article' detecte)")
            sparse_results = search_sparse(query)
            fused = sparse_results
            for r in fused:
                r["score_rrf"] = r["score"]
            log_fusion_stats([], sparse_results, fused)

        else:
            print("→ Hybrid search (dense + sparse + RRF)")
            dense_results = await search_dense(query)
            sparse_results = search_sparse(query)
            fused = rrf_fusion(dense_results, sparse_results)
            log_fusion_stats(dense_results, sparse_results, fused)

        # ── Résultats ──────────────────────────────────────────────
        print("Top-10 resultats :\n")
        for i, r in enumerate(fused[:10], 1):
            print(
                f"[{i}] {r['source']} p.{r['page']}"
                f" — score={r['score_rrf']:.6f}"
            )
            print(f"     {r['content'][:150]}...")

    finally:
        await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())