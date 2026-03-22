import re 

from pathlib import Path  

from fastapi import (
    APIRouter,   
    HTTPException,  
    UploadFile,  
    File,        
)

from app.core.config import get_settings  
from app.schemas.chat import IngestResponse  
from app.rag.loader import (
    load_file,           
    SUPPORTED_EXTENSIONS,  
)
from app.rag.dense_retriever import (
    index_documents,      
    delete_document,      
)
from app.rag.sparse_retriever import (
    index_documents_sparse,   
)


router = APIRouter()  

MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def _get_upload_dir() -> Path:
    settings = get_settings()  
    path = Path(settings.raw_data_path)  
    path.mkdir(parents=True, exist_ok=True)  
    return path  



def _validate_filename(filename: str) -> None:
    if not re.match(r'^[a-zA-Z0-9_\-. ]+$', filename):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Le nom du fichier '{filename}' contient "
                f"des accents ou caractères spéciaux. "
                f"Renomme le fichier en utilisant uniquement "
                f"des lettres sans accents, chiffres, "
                f"tirets et underscores. "
                f"Exemple : 'Procedure_civile.docx' "
                f"au lieu de 'Procédure_civile_WORD.docx'."
            ),
        )


def _validate_file(file: UploadFile) -> None:
    suffix = Path(file.filename).suffix.lower()  
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,  
            detail=(
                f"Format non supporté : '{suffix}'. "
                f"Acceptés : {', '.join(SUPPORTED_EXTENSIONS)}"
            ),
        )


async def _save_file(file: UploadFile, dest: Path) -> None:
    total_size = 0 
    chunk_size = 1024 * 1024  

    with dest.open("wb") as f:  
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break  

            total_size += len(chunk)  

            if total_size > MAX_FILE_SIZE_BYTES:
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,  
                    detail=(
                        f"Fichier trop volumineux. "
                        f"Limite : {MAX_FILE_SIZE_MB} Mo."
                    ),
                )

            f.write(chunk)  


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file(
    file: UploadFile = File(...),
) -> IngestResponse:
    _validate_file(file)  
    _validate_filename(file.filename)  

    upload_dir = _get_upload_dir()  
    dest = upload_dir / file.filename  

    try:
        await _save_file(file, dest)  

    except HTTPException:
        raise  

    except Exception as e:
        dest.unlink(missing_ok=True)  
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la sauvegarde : {str(e)}",
        )

    try:
        chunks = load_file(str(dest)) 

    except Exception as e:
        dest.unlink(missing_ok=True)  
        raise HTTPException(
            status_code=422,  
            detail=f"Erreur lors du chargement : {str(e)}",
        )

    doc_id = chunks[0].metadata["doc_id"] if chunks else None

    try:
        n_dense = await index_documents(chunks)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur indexation dense : {str(e)}",
        )

    try:
        n_sparse = await index_documents_sparse(chunks)

    except Exception as e:
        if n_dense > 0 and doc_id:
            await delete_document(doc_id)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur indexation sparse : {str(e)}",
        )

    if n_dense == 0 and n_sparse == 0:
        return IngestResponse(
            file=file.filename,
            chunks_dense=0,
            chunks_sparse=0,
            status="already_indexed",  
        )

    return IngestResponse(
        file=file.filename,     
        chunks_dense=n_dense,   
        chunks_sparse=n_sparse, 
        status="ok",            
    )


@router.post("/ingest/path", response_model=IngestResponse)
async def ingest_path(body: dict) -> IngestResponse:
    file_path = body.get("file_path", "")  
    _validate_filename(path.name) 

    if not file_path:
        raise HTTPException(
            status_code=400,
            detail="Champ 'file_path' manquant dans le body.",
        )

    path = Path(file_path).resolve()  

    upload_dir = _get_upload_dir().resolve()  

    if not str(path).startswith(str(upload_dir)):
        raise HTTPException(
            status_code=403,  
            detail=(
                "Accès refusé. Seuls les fichiers dans "
                "data/raw/ peuvent être indexés."
            ),
        )

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Fichier introuvable : {path.name}",
        )

    try:
        chunks = load_file(str(path))  
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Erreur lors du chargement : {str(e)}",
        )

    doc_id = chunks[0].metadata["doc_id"] if chunks else None

    try:
        n_dense = await index_documents(chunks)  
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur indexation dense : {str(e)}",
        )

    try:
        n_sparse = await index_documents_sparse(chunks)  
    except Exception as e:
        if n_dense > 0 and doc_id:
            await delete_document(doc_id)  
        raise HTTPException(
            status_code=500,
            detail=f"Erreur indexation sparse : {str(e)}",
        )

    if n_dense == 0 and n_sparse == 0:
        return IngestResponse(
            file=path.name,
            chunks_dense=0,
            chunks_sparse=0,
            status="already_indexed",
        )

    return IngestResponse(
        file=path.name,
        chunks_dense=n_dense,
        chunks_sparse=n_sparse,
        status="ok",
    )