from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.messages import (
    HumanMessage,   
    AIMessage,      
    BaseMessage,    
)

from app.core.config import get_settings  


_ROUTER_PROMPT = """Tu es un classificateur d'intentions pour \
un chatbot juridique étudiant en droit français.
Réponds UNIQUEMENT par un seul mot parmi : chat, rag, summarize, fiche.
N'ajoute aucune explication, aucune ponctuation, aucun autre mot.

Exemples :
"bonjour"                                    → chat
"merci"                                      → chat
"ça va ?"                                    → chat
"tu peux faire quoi ?"                       → chat
"que dit l'article 372 du CPC ?"            → rag
"quelles sont les conditions de la faute ?" → rag
"explique la théorie de l'imprévision"      → rag
"définition de la responsabilité civile"    → rag
"résume le cours de procédure civile"       → summarize
"fais un résumé du PDF"                     → summarize
"synthèse du document"                      → summarize
"donne moi un résumé"                       → summarize
"fais une fiche sur la faute délictuelle"   → fiche
"fiche de révision sur les contrats"        → fiche
"je veux réviser la responsabilité"         → fiche
"fiche sur l'article 1240"                  → fiche

Message : "{message}"
Intent :"""


_VALID_INTENTS = {"chat", "rag", "summarize", "fiche"}

_DEFAULT_INTENT = "rag"


def _build_llm() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0,
        max_output_tokens=5,
    )


async def detect_intent(
    message: str,
    history: list[BaseMessage] | None = None,
) -> str:
    context = ""  

    if history:
        last_two = history[-2:]

        lines = []  
        for msg in last_two:
            if isinstance(msg, HumanMessage):
                lines.append(f"étudiant: {msg.content}")
            elif isinstance(msg, AIMessage):
                lines.append(
                    f"assistant: {msg.content[:100]}..."
                )

        if lines:
            context = (
                "\nContexte des derniers échanges :\n"
                + "\n".join(lines)
                + "\n"
            )

    prompt = _ROUTER_PROMPT.format(
        message=message  
    )

    prompt = prompt.replace(
        f'Message : "{message}"',  
        f'{context}Message : "{message}"',  
    )

    llm = _build_llm()  

    try:
        response = await llm.ainvoke(
            [HumanMessage(content=prompt)]
        )

        intent = response.content.strip().lower()

        if intent not in _VALID_INTENTS:
            return _DEFAULT_INTENT  

        return intent  

    except Exception:
        return _DEFAULT_INTENT