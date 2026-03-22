import json  
from pathlib import Path  
from dataclasses import dataclass  

from app.core.config import get_settings  

_DEFAULT_SYSTEM_PROMPT = """Tu es un assistant juridique intelligent \
conçu pour aider un étudiant en droit français.

Règles absolues :
- Tu réponds TOUJOURS en français.
- Tu cites TOUJOURS tes sources avec [N] quand tu utilises \
search_documents.
- Tu ne réponds JAMAIS à une question juridique sans avoir \
d'abord consulté les documents via search_documents.
- Pour les questions de conversation courante (bonjour, merci, \
ça va), tu réponds directement sans appeler de tool.
- Quand l'utilisateur mentionne un article de loi, tu reformules \
sa question en supprimant les apostrophes avant de chercher.
  Exemple : "l'article 372" → tu cherches "article 372".
- Tu es précis, concis et pédagogique dans tes réponses.
- Si un document est introuvable ou ne contient pas l'information, \
tu le dis clairement."""

_DEFAULT_RAG_PROMPT = """Voici les passages pertinents trouvés \
dans les documents juridiques :

{context}

En te basant UNIQUEMENT sur ces passages, réponds à la question \
suivante de manière claire et structurée.
Cite chaque passage utilisé avec son numéro [N].
Si les passages ne permettent pas de répondre complètement, \
indique-le explicitement.

Question : {question}

Réponse :"""


@dataclass
class Prompts:
    system_prompt: str  
    rag_prompt: str    


class PromptStore:
    """
    Gestionnaire de persistance des prompts éditables.
    Lit et écrit dans config/prompts.json.
    Chaque appel à load() relit le fichier — les modifications
    Streamlit sont prises en compte sans redémarrer le serveur.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._path = Path(settings.prompts_path)

    def load(self) -> Prompts:
        if not self._path.exists():
            return self._get_defaults()

        try:
            with self._path.open("r", encoding="utf-8") as f:
                data = json.load(f)  

            return Prompts(
                system_prompt=data.get(
                    "system_prompt",
                    _DEFAULT_SYSTEM_PROMPT,
                ),
                rag_prompt=data.get(
                    "rag_prompt",
                    _DEFAULT_RAG_PROMPT,
                ),
            )

        except (json.JSONDecodeError, KeyError):
            return self._get_defaults()

    def save(
        self,
        system_prompt: str,
        rag_prompt: str,
    ) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "system_prompt": system_prompt,  
            "rag_prompt": rag_prompt,       
        }

        with self._path.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,  
                indent=2,            
            )

    def reset(self) -> Prompts:
        defaults = self._get_defaults()  
        self.save(defaults.system_prompt, defaults.rag_prompt)
        return defaults  

    @staticmethod
    def _get_defaults() -> Prompts:
        return Prompts(
            system_prompt=_DEFAULT_SYSTEM_PROMPT,  
            rag_prompt=_DEFAULT_RAG_PROMPT,        
        )


prompt_store = PromptStore()  