from typing import Optional  

from langchain_core.messages import (
    BaseMessage,      
    HumanMessage,     
    AIMessage,        
)

from app.db.session import get_pool 


async def save_message(
    session_id: str,
    role: str,
    content: str,
    intent: Optional[str] = None,
) -> None:
    pool = get_pool()  

    async with pool.acquire() as conn:  
        await conn.execute(
            """
            INSERT INTO conversations
                (session_id, role, content, intent)
            VALUES
                ($1, $2, $3, $4)
            """,
            session_id,  
            role,        
            content,     
            intent,      
        )


async def get_history(
    session_id: str,
    limit: int = 20,
) -> list[BaseMessage]:
    pool = get_pool()  

    async with pool.acquire() as conn:  
        rows = await conn.fetch(
            """
            SELECT role, content
            FROM conversations
            WHERE session_id = $1
            ORDER BY created_at ASC  -- ordre chronologique
            LIMIT $2
            """,
            session_id,  
            limit,       
        )

    messages = []  

    for row in rows:
        if row["role"] == "human":
            messages.append(HumanMessage(content=row["content"]))
        else:
            messages.append(AIMessage(content=row["content"]))

    return messages  


async def get_history_raw(
    session_id: str,
    limit: int = 20,
) -> list[dict]:
    pool = get_pool()  

    async with pool.acquire() as conn:  
        rows = await conn.fetch(
            """
            SELECT role, content, intent, created_at
            FROM conversations
            WHERE session_id = $1
            ORDER BY created_at ASC
            LIMIT $2
            """,
            session_id,  
            limit,       
        )

    return [
        {
            "role": row["role"],              
            "content": row["content"],        
            "intent": row["intent"],          
            "created_at": row["created_at"].isoformat(),  
        }
        for row in rows  
    ]


async def delete_session(session_id: str) -> int:
    pool = get_pool()  

    async with pool.acquire() as conn:  
        result = await conn.execute(
            """
            DELETE FROM conversations
            WHERE session_id = $1
            """,
            session_id,  
        )
        deleted = int(result.split()[-1])

    return deleted  


async def list_sessions() -> list[dict]:
    pool = get_pool()  

    async with pool.acquire() as conn:  
        rows = await conn.fetch(
            """
            SELECT
                session_id,
                COUNT(*) AS message_count,
                MIN(created_at) AS started_at,
                MAX(created_at) AS last_message_at
            FROM conversations
            GROUP BY session_id
            ORDER BY last_message_at DESC
            """
        )

    return [
        {
            "session_id": row["session_id"],
            "message_count": row["message_count"],
            "started_at": row["started_at"].isoformat(),
            "last_message_at": row["last_message_at"].isoformat(),
        }
        for row in rows  
    ]