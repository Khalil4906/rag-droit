from pydantic import BaseModel, Field  


class Message(BaseModel):
    role: str = Field(
        ...,  
        pattern="^(human|assistant)$",  
        description="Rôle de l'auteur du message",
    )
    content: str = Field(
        ...,  
        min_length=1,  
        description="Contenu du message",
    )


class ChatRequest(BaseModel):
    session_id: str = Field(
        ...,  
        min_length=1,  #
        description="Identifiant unique de session Streamlit",
    )
    message: str = Field(
        ...,  
        min_length=1,   
        max_length=4000,  
        description="Message de l'étudiant",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "session_abc123",
                "message": "que dit l'article 372 du CPC ?",
            }
        }
    }


class ChatResponse(BaseModel):
    answer: str = Field(
        ...,  
        description="Réponse générée par l'agent",
    )
    intent: str = Field(
        ...,  
        description="Intent détecté : chat/rag/summarize/fiche",
    )
    sources_used: bool = Field(
        ...,  
        description="True si des documents ont été consultés",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "L'article 372 dispose que...",
                "intent": "rag",
                "sources_used": True,
            }
        }
    }



class HistoryResponse(BaseModel):
    session_id: str = Field(
        ...,
        description="Identifiant de session",
    )
    messages: list[Message] = Field(
        default_factory=list,  
        description="Liste des messages de la session",
    )



class IngestResponse(BaseModel):
    file: str = Field(
        ...,
        description="Nom du fichier indexé",
    )
    chunks_dense: int = Field(
        ...,
        description="Nombre de chunks indexés dans pgvector",
    )
    chunks_sparse: int = Field(
        ...,
        description="Nombre de chunks indexés dans BM25",
    )
    status: str = Field(
        default="ok",
        description="Statut de l'indexation",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "file": "cours_contrats.pdf",
                "chunks_dense": 47,
                "chunks_sparse": 47,
                "status": "ok",
            }
        }
    }



class DocumentInfo(BaseModel):
    doc_id: str = Field(
        ...,
        description="Identifiant stable du document",
    )
    source: str = Field(
        ...,
        description="Nom du fichier",
    )
    chunk_count: int = Field(
        ...,
        description="Nombre de chunks indexés",
    )
    page_count: int = Field(
        ...,
        description="Nombre de pages approximatif",
    )
    indexed_at: str = Field(
        ...,
        description="Date d'indexation ISO 8601",
    )


class DocumentsResponse(BaseModel):
    documents: list[DocumentInfo] = Field(
        default_factory=list,
        description="Liste des documents indexés",
    )
    total: int = Field(
        ...,
        description="Nombre total de documents",
    )


class DeleteDocumentResponse(BaseModel):
    doc_id: str = Field(
        ...,
        description="Identifiant du document supprimé",
    )
    chunks_deleted_dense: int = Field(
        ...,
        description="Chunks supprimés de pgvector",
    )
    chunks_deleted_sparse: int = Field(
        ...,
        description="Chunks supprimés de BM25",
    )
    status: str = Field(
        default="ok",
        description="Statut de la suppression",
    )


class PromptConfig(BaseModel):
    system_prompt: str = Field(
        ...,
        min_length=1,
        description="Prompt système de l'agent",
    )
    rag_prompt: str = Field(
        ...,
        min_length=1,
        description="Template de prompt RAG",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "system_prompt": "Tu es un assistant juridique...",
                "rag_prompt": "Voici les passages trouvés : {context}",
            }
        }
    }


class SessionInfo(BaseModel):
    session_id: str = Field(
        ...,
        description="Identifiant de session",
    )
    message_count: int = Field(
        ...,
        description="Nombre de messages dans la session",
    )
    started_at: str = Field(
        ...,
        description="Date de début ISO 8601",
    )
    last_message_at: str = Field(
        ...,
        description="Date du dernier message ISO 8601",
    )


class SessionsResponse(BaseModel):
    sessions: list[SessionInfo] = Field(
        default_factory=list,
        description="Liste des sessions",
    )
    total: int = Field(
        ...,
        description="Nombre total de sessions",
    )