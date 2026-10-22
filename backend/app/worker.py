from arq.connections import RedisSettings
import pymupdf4llm
from pathlib import Path
from app.database import SessionLocal
from app.models import Document, DocumentChunk
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
import asyncio
import sys

if sys.platform=="win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

REDIS_SETTINGS=RedisSettings(
    host="127.0.0.1",
    port=6379
)

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

def extract_text(file:Path)->str|None:
    """
    Returns extracted text from the given PDF file
    """
    text=pymupdf4llm.to_markdown(file)

    text=text.strip()

    if text =="":
        return None

    return text

async def save_document_text(document_id:int, extracted_text:str):
    """
    - Stores extracted text in documents
    """
    async with SessionLocal() as db:
        await db.execute(update(Document).where(Document.id==document_id, Document.extracted_text.is_(None)).values(extracted_text=extracted_text))

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
            {
                "document_id":document_id,
                "chunk_index":i,
                "content":chunk
            }
        )


    async with SessionLocal() as db:

        await db.execute(insert(DocumentChunk).values(document_chunks).
        on_conflict_do_nothing(index_elements=["document_id","chunk_index"]))

        await db.commit()

async def process_document(ctx,document_id:int):
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

    if extracted_text is None:
        return

    await save_document_text(document_id, extracted_text)

    chunks=await asyncio.to_thread(chunk_text,extracted_text)

    await save_document_chunks(document_id,chunks)

async def startup(ctx):
    pass

async def shutdown(ctx):
    pass

class WorkerSettings:
    functions=[process_document]
    on_startup=startup
    on_shutdown=shutdown
    redis_settings=REDIS_SETTINGS