import hashlib  
from pathlib import Path  

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
)
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter, 
)
from langchain_core.documents import Document 

from app.core.config import get_settings


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def _generate_doc_id(file_path: str) -> str:
    return hashlib.md5(
        str(Path(file_path).resolve()).encode()
    ).hexdigest()


def _validate_extension(path: Path) -> None:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS: 
        raise ValueError(
            f"Format non supporté : '{path.suffix}'. "
            f"Acceptés : {', '.join(SUPPORTED_EXTENSIONS)}"
        )


def _load_raw(path: Path) -> list[Document]:
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        loader = PyPDFLoader(str(path), extract_images=False)
    elif suffix == ".docx":
        loader = Docx2txtLoader(str(path))
    else:
        loader = TextLoader(str(path), encoding="utf-8")

    return loader.load()


def _enrich_metadata(
    docs: list[Document],
    doc_id: str,
    source: str,
) -> list[Document]:
    for doc in docs:
        doc.metadata["doc_id"] = doc_id 
        doc.metadata["source"] = source 

        if "page" in doc.metadata:
            doc.metadata["page"] = doc.metadata["page"] + 1
        else:
            doc.metadata["page"] = 0 

    return docs


def _split(docs: list[Document]) -> list[Document]:
    settings = get_settings()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,        
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
        add_start_index=True,
    )

    chunks = splitter.split_documents(docs)

    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i  

    return chunks


def load_file(file_path: str) -> list[Document]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    _validate_extension(path)

    doc_id = _generate_doc_id(file_path)
    source = path.name                     

    docs = _load_raw(path)                 
    docs = _enrich_metadata(              
        docs, doc_id, source
    )
    chunks = _split(docs)                

    return chunks