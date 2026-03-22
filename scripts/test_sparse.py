import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv() 

from app.rag.loader import load_file
from app.rag.sparse_retriever import (
    index_documents_sparse,
    search_sparse,
    list_documents_sparse,
)


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage : python scripts/test_sparse.py "
            "<fichier> \"<question>\""
        )
        sys.exit(1)

    file_path = sys.argv[1]  
    query = sys.argv[2]      

    print(f"Indexation BM25 : {file_path}")
    chunks = load_file(file_path)       
    n = index_documents_sparse(chunks)  
    print(f"OK — {n} chunks indexes.")

    doc_ids = list_documents_sparse()  
    print(f"Documents dans l'index : {len(doc_ids)}")

    print(f"\nRecherche BM25 : \"{query}\"")
    results = search_sparse(query)
    print(f"Top-{len(results)} resultats :\n")

    for i, r in enumerate(results[:5], 1): 
        print(
            f"[{i}] {r['source']} p.{r['page']}"
            f" — score={r['score']:.3f}"
        )
        print(f"     {r['content'][:150]}...")


if __name__ == "__main__":
    main()