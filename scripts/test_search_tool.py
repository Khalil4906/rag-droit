import asyncio  
import sys  
from pathlib import Path  

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  
load_dotenv()  

from app.db.session import connect_db, disconnect_db  
from app.tools.search_documents import search_documents  


async def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage :\n"
            "  python scripts/test_search_tool.py \"<question>\"\n"
            "  python scripts/test_search_tool.py "
            "\"<question>\" \"<nom_doc>\""
        )
        sys.exit(1)

    query = sys.argv[1]  
    doc_filter = (
        sys.argv[2] if len(sys.argv) > 2 else None
    )  

    await connect_db()

    try:
        print(f"Query      : {query}")
        print(f"Doc filter : {doc_filter or 'aucun (tous les docs)'}")
        print("-" * 60)

        result = await search_documents.ainvoke({
            "query": query,  
            "doc_filter": doc_filter,  
        })

        print(result)

    finally:
        await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())  