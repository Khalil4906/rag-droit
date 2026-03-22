import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.db.session import connect_db, disconnect_db
from app.rag.loader import load_file
from app.rag.dense_retriever import (
    index_documents,
    search_dense,
    list_documents,
)


async def main() -> None:
    if len(sys.argv) < 3:  
        print(
            "Usage : python scripts/test_dense.py "
            "<fichier> \"<question>\""
        )
        sys.exit(1)

    file_path = sys.argv[1]   
    query = sys.argv[2]       

    await connect_db()  

    try:
        print(f"Indexation de : {file_path}")
        chunks = load_file(file_path)  
        n = await index_documents(chunks)  
        print(f"OK — {n} chunks indexes.")

        docs = await list_documents()  
        print(f"\nDocuments indexes : {len(docs)}")
        for doc in docs:
            print(
                f"  {doc['source']} — "
                f"{doc['chunk_count']} chunks"
            )

        print(f"\nRecherche : \"{query}\"")
        results = await search_dense(query)  
        print(f"Top-{len(results)} resultats :\n")

        for i, r in enumerate(results, 1):
            print(f"[{i}] {r['source']} p.{r['page']}"
                  f" — score={r['score']:.3f}")
            print(f"     {r['content'][:150]}...")

    finally:
        await disconnect_db()  


if __name__ == "__main__":
    asyncio.run(main())