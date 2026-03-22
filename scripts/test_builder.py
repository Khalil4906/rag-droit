import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.db.session import connect_db, disconnect_db
from app.agents.router import detect_intent
from app.agents.builder import run_agent
from app.db.conversations import get_history


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage : python scripts/test_builder.py \"<message>\"")
        sys.exit(1)

    message = sys.argv[1]
    session_id = "test_session_builder"

    await connect_db()

    try:
        history = await get_history(session_id)
        intent = await detect_intent(message, history=history)

        print(f"Message : {message}")
        print(f"Intent  : {intent}")
        print("-" * 60)

        result = await run_agent(
            message=message,
            intent=intent,
            history=history,
            session_id=session_id,
        )

        print(f"Réponse :\n{result['answer']}")
        print("-" * 60)
        print(f"Sources utilisées : {result['sources_used']}")

    finally:
        await disconnect_db()


if __name__ == "__main__":
    asyncio.run(main())