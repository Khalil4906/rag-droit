import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage, AIMessage
from app.agents.router import detect_intent

_TEST_MESSAGES = [
    ("bonjour", None, "chat"),
    ("merci pour ton aide", None, "chat"),
    ("tu peux faire quoi ?", None, "chat"),
    ("que dit l'article 372 du CPC ?", None, "rag"),
    ("conditions de la responsabilité civile", None, "rag"),
    ("explique la théorie de l'imprévision", None, "rag"),
    ("définition du dol en droit des contrats", None, "rag"),
    ("résume le cours de procédure civile", None, "summarize"),
    ("fais un résumé du document", None, "summarize"),
    ("synthèse du PDF", None, "summarize"),
    ("fais une fiche sur la faute délictuelle", None, "fiche"),
    ("fiche de révision sur les contrats", None, "fiche"),
    ("je veux réviser la responsabilité", None, "fiche"),
    (
        "et le 373 ?",
        [
            HumanMessage(content="que dit l'article 372 ?"),
            AIMessage(content="L'article 372 dispose que..."),
        ],
        "rag",
    ),
    (
        "la responsabilité",
        [
            HumanMessage(content="fais moi une fiche"),
            AIMessage(content="Sur quel sujet ?"),
        ],
        "fiche",
    ),
    (
        "oui ce document",
        [
            HumanMessage(content="résume le cours"),
            AIMessage(content="Quel document voulez-vous ?"),
        ],
        "summarize",
    ),
]


async def main() -> None:
    print("Test router\n")
    print(f"{'Message':<45} {'Attendu':<12} {'Obtenu':<12} {'OK'}")
    print("-" * 80)

    correct = 0
    total = len(_TEST_MESSAGES)

    for message, history, expected in _TEST_MESSAGES:
        result = await detect_intent(message, history=history)
        ok = result == expected
        if ok:
            correct += 1
        status = "OK" if ok else "ERREUR"
        print(
            f"{message:<45} {expected:<12} {result:<12} {status}"
        )

    print("-" * 80)
    print(f"\nScore : {correct}/{total}")


if __name__ == "__main__":
    asyncio.run(main())