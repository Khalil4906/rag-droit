import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.loader import load_file  


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage : python scripts/test_loader.py <chemin_fichier>")
        sys.exit(1)

    file_path = sys.argv[1] 

    print(f"Chargement de : {file_path}")
    chunks = load_file(file_path)

    print(f"\nNombre de chunks : {len(chunks)}")
    print("-" * 60)

    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i} :")
        print(f"  doc_id      : {chunk.metadata['doc_id']}")
        print(f"  source      : {chunk.metadata['source']}")
        print(f"  page        : {chunk.metadata['page']}")
        print(f"  chunk_index : {chunk.metadata['chunk_index']}")
        print(f"  taille      : {len(chunk.page_content)} chars")
        print(f"  contenu     : {chunk.page_content[:200]}...")

    print("\n" + "-" * 60)
    print(f"OK — {len(chunks)} chunks prets pour l'indexation.")


if __name__ == "__main__":
    main()