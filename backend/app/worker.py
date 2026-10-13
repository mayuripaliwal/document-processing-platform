from arq.connections import RedisSettings
import pymupdf4llm
from pathlib import Path
from app.database import SessionLocal
from app.models import Document, DocumentChunk
from sqlalchemy import select, update
import asyncio

REDIS_SETTINGS=RedisSettings()

async def extract_document_storage_path(document_id:int)->Path | None:
    """
    - Extracts the document storage path for a given document ID from db
    - Returns None if document does not exist
    """
    async with SessionLocal() as db:
        result=await db.execute(select(Document.storage_path).where(Document.id==document_id))
        storage_path=result.scalar_one_or_none()

        if storage_path is None:
            return None
        
        return Path(storage_path)

def extract_text(file:Path)->str:
    """
    Returns extracted text from the given PDF file
    """
    text=pymupdf4llm.to_markdown(file)
    return text

async def save_document_text(document_id:int, extracted_text:str):
    """
    - Stores extracted text in documents
    """
    async with SessionLocal() as db:
        await db.execute(update(Document).where(Document.id==document_id).values(extracted_text=extracted_text))

        await db.commit()

def chunk_text(text:str)->list[str]:
    """
    Returns a list of text chunks with maximum chunk size 100
    """
    chunks=[]

    chunk_size=100

    tokens=text.split()

    start=0

    while start<len(tokens):
        curr_words=" ".join(tokens[start:start+chunk_size])
        chunks.append(curr_words)
        start+=chunk_size

    return chunks

async def save_document_chunks(document_id:int,chunks:list[str]):
    """
    Stores document chunks of a given document id in document_chunks
    """

    document_chunks=[]
    for i,chunk in enumerate(chunks):
        document_chunks.append(
            DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                content=chunk
            )
        )


    async with SessionLocal() as db:
        db.add_all(document_chunks)

        await db.commit()

async def process_document(document_id:int):
    """
    - Extracts document text from the document for a given document_id
    - Stores the extracted_text in documents table
    - Stores its text chunks in document_chunks table
    """
    storage_path=await extract_document_storage_path(document_id)

    if storage_path is None:
        #document does not exist, means it got deleted after it was added 
        # and before worker could process it
        return

    extracted_text=await asyncio.to_thread(extract_text,storage_path)

    await save_document_text(document_id, extracted_text)

    chunks=await asyncio.to_thread(chunk_text,extracted_text)

    await save_document_chunks(document_id,chunks)

async def startup():
    pass

async def shutdown():
    pass

class WorkerSettings:
    functions=[process_document]
    on_startup=startup
    on_shutdown=shutdown
    redis_settings=REDIS_SETTINGS