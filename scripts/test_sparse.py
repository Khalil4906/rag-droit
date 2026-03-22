import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.rag.loader import load_file, SUPPORTED_EXTENSIONS
from app.rag.sparse_retriever import (
    index_documents_sparse,
    search_sparse,
    list_documents_sparse,
)
from app.db.session import connect_db, disconnect_db


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
            "Usage : python scripts/test_sparse.py "
            "<fichier> \"<question>\""
        )
        sys.exit(1)

    file_path = sys.argv[1]
    query = sys.argv[2]

    files = resolve_files(file_path)

    await connect_db()

    try:
        print(f"Indexation BM25 de {len(files)} fichier(s) :")
        total = 0
        for file in files:
            print(f"  → {file.name}")
            chunks = load_file(str(file))
            n = await index_documents_sparse(chunks)
            total += n
            print(f"     {n} chunks")

        print(f"OK — {total} chunks indexes.")

        doc_ids = await list_documents_sparse()
        print(f"Documents dans l'index : {len(doc_ids)}")

        print(f"\nRecherche BM25 : \"{query}\"")
        results = await search_sparse(query)
        print(f"Top-{len(results)} resultats :\n")

        for i, r in enumerate(results[:5], 1):
            print(
                f"[{i}] {r['source']} p.{r['page']}"
                f" — score={r['score']:.3f}"
            )
            print(f"     {r['content'][:150]}...")

    finally:
        await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())