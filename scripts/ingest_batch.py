import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.rag.loader import load_file, SUPPORTED_EXTENSIONS
from app.rag.dense_retriever import index_documents
from app.rag.sparse_retriever import index_documents_sparse
from app.db.session import connect_db, disconnect_db


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage : python scripts/ingest_batch.py <dossier>")
        sys.exit(1)

    folder = Path(sys.argv[1])

    if not folder.is_dir():
        print(f"Dossier introuvable : {folder}")
        sys.exit(1)

    files = [
        f for f in folder.iterdir()
        if f.is_file()
        and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print(f"Aucun fichier supporté dans : {folder}")
        sys.exit(1)

    await connect_db()

    try:
        print(f"Indexation de {len(files)} fichier(s) :\n")
        total_dense = 0
        total_sparse = 0

        for file in files:
            print(f"→ {file.name}")
            chunks = load_file(str(file))
            n_dense = await index_documents(chunks)
            n_sparse = await index_documents_sparse(chunks)
            total_dense += n_dense
            total_sparse += n_sparse
            print(f"   dense={n_dense} sparse={n_sparse} chunks")

        print(f"\nOK — total dense={total_dense} sparse={total_sparse}")

    finally:
        await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())