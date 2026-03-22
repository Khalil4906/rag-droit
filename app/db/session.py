import asyncpg  
import ssl  
from typing import AsyncGenerator  
from app.core.config import get_settings  

_pool: asyncpg.Pool | None = None


def _build_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()  
    ctx.check_hostname = True  
    ctx.verify_mode = ssl.CERT_REQUIRED  
    return ctx  


async def connect_db() -> None:
    global _pool 

    settings = get_settings()

    _pool = await asyncpg.create_pool(
        dsn=settings.get_asyncpg_url(),
        min_size=2,    
        max_size=10,   
        ssl=_build_ssl_context(),  
        command_timeout=60,  
        server_settings={
            "application_name": "rag_droit", 
        },
    )


async def disconnect_db() -> None:
    global _pool  
    if _pool is not None:  
        await _pool.close()  
        _pool = None 


def get_pool() -> asyncpg.Pool:
    if _pool is None: 
        raise RuntimeError("Pool non initialisé")
    return _pool 


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    pool = get_pool() 
    async with pool.acquire() as conn:  
        yield conn 