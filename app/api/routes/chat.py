from fastapi import APIRouter, HTTPException  

from app.schemas.chat import (
    ChatRequest,      
    ChatResponse,     
    HistoryResponse,  
    Message,          
    SessionsResponse, 
    SessionInfo,      
)
from app.agents.router import detect_intent   
from app.agents.builder import run_agent      
from app.db.conversations import (
    get_history,       
    get_history_raw,   
    delete_session,    
    list_sessions,     
)


router = APIRouter()  


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        history = await get_history(
            session_id=request.session_id,
            limit=20, 
        )

    except Exception:
        raise HTTPException(
            status_code=503,  
            detail=(
                "Base de données indisponible. "
                "Réessaie dans quelques instants."
            ),
        )

    try:
        intent = await detect_intent(
            message=request.message,
            history=history,  
        )

    except Exception:
        intent = "rag"

    try:
        result = await run_agent(
            message=request.message,   
            intent=intent,             
            history=history,           
            session_id=request.session_id,  
        )

    except TimeoutError:
        raise HTTPException(
            status_code=504,  
            detail=(
                "Le service de génération a mis trop de temps "
                "à répondre. Réessaie dans quelques instants."
            ),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,  
            detail=f"Erreur interne : {str(e)}",
        )

    return ChatResponse(
        answer=result["answer"],            
        intent=result["intent"],            
        sources_used=result["sources_used"],  
    )


@router.get(
    "/history/{session_id}",
    response_model=HistoryResponse,
)
async def get_chat_history(session_id: str) -> HistoryResponse:
    try:
        raw = await get_history_raw(
            session_id=session_id,
            limit=20,  
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Base de données indisponible.",
        )

    messages = [
        Message(
            role=m["role"],      
            content=m["content"],  
        )
        for m in raw  
    ]

    return HistoryResponse(
        session_id=session_id,  
        messages=messages,      
    )


@router.delete("/history/{session_id}")
async def delete_chat_history(session_id: str) -> dict:
    try:
        deleted = await delete_session(session_id=session_id)

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Base de données indisponible.",
        )

    return {
        "session_id": session_id,   
        "messages_deleted": deleted,  
        "status": "ok",
    }


@router.get("/sessions", response_model=SessionsResponse)
async def get_sessions() -> SessionsResponse:
    try:
        sessions_raw = await list_sessions()

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Base de données indisponible.",
        )

    sessions = [
        SessionInfo(
            session_id=s["session_id"],
            message_count=s["message_count"],
            started_at=s["started_at"],
            last_message_at=s["last_message_at"],
        )
        for s in sessions_raw
    ]

    return SessionsResponse(
        sessions=sessions,       
        total=len(sessions),     
    )