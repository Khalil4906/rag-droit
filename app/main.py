from contextlib import asynccontextmanager  

from fastapi import FastAPI  
from fastapi.middleware.cors import CORSMiddleware  

from app.core.config import get_settings  
from app.db.session import (
    connect_db,     
    disconnect_db,  
)

from app.api.routes import (
    chat,            
    ingest,          
    config_routes,   
    documents,       
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


app = FastAPI(
    title="RAG Droit",  
    description=(
        "Chatbot RAG pour étudiant en droit — "
        "hybrid search pgvector + BM25"
    ),
    version="1.0.0",  
    lifespan=lifespan,  
)


settings = get_settings()  

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,   
    allow_methods=["*"],      
    allow_headers=["*"],      
)


app.include_router(
    chat.router,
    prefix="/api/v1",  
    tags=["Chat"],     
)

app.include_router(
    ingest.router,
    prefix="/api/v1",
    tags=["Ingestion"],
)

app.include_router(
    config_routes.router,
    prefix="/api/v1",
    tags=["Configuration"],
)

app.include_router(
    documents.router,
    prefix="/api/v1",
    tags=["Documents"],
)


@app.get("/health", tags=["Monitoring"])
async def health() -> dict:
    return {"status": "ok"}  