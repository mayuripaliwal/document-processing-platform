from arq.connections import RedisSettings
import pymupdf4llm
from pathlib import Path
from app.database import SessionLocal
from app.models import Document, DocumentChunk
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
import asyncio
import sys
from app.embeddings import load_embedding_model
import logging

logger=logging.getLogger(__name__)

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

async def save_document_chunk_details(document_id:int,chunks:list[str], embeddings:list[list[float]]):
    """
    Stores document chunk details[chunk, embedding] of a given document id in document_chunks
    """

    document_chunk_details=[]
    for chunk_index, (chunk,embedding) in enumerate(zip(chunks, embeddings)):
        document_chunk_details.append(
            {
                "document_id":document_id,
                "chunk_index":chunk_index,
                "content":chunk,
                "embedding":embedding
            }
        )


    async with SessionLocal() as db:

        await db.execute(insert(DocumentChunk).values(document_chunk_details).
        on_conflict_do_nothing(index_elements=["document_id","chunk_index"]))

        await db.commit()

async def process_document(ctx,document_id:int):
    """
    - Extracts document text from the document for a given document_id
    - Stores the extracted_text in documents table
    - Stores its text chunks in document_chunks table
    """    
    storage_path=await extract_document_storage_path(document_id)
    logger.info("Extracted storage path for document_id: %s", document_id)

    if storage_path is None:
        #document does not exist, means it got deleted after it was added 
        # and before worker could process it
        return

    extracted_text=await asyncio.to_thread(extract_text,storage_path)

    if extracted_text is None:
        return

    logger.info("Extracted text for document_id: %s", document_id)

    await save_document_text(document_id, extracted_text)

    logger.info("Saved extracted text for document_id: %s", document_id)

    #store chunks and their embeddings
    
    chunks=await asyncio.to_thread(chunk_text,extracted_text)

    logger.info("Extracted chunks for document_id: %s", document_id)

    model=ctx["embedding_model"]

    embeddings=await asyncio.to_thread(model.encode, chunks)

    logger.info("Extracted embeddings for document_id: %s", document_id)

    await save_document_chunk_details(document_id,chunks, embeddings.tolist())

    logger.info("Saved chunks and embeddings for document_id: %s", document_id)

async def startup(ctx):
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s %(funcName)s: %(message)s",level=logging.INFO)
    
    logger.info("Started ARQ Worker")
    
    ctx["embedding_model"]=load_embedding_model()

    logger.info("Embedding model loaded")
    
    
async def shutdown(ctx):
    logger.info("Stopped ARQ Worker")
    pass

class WorkerSettings:
    functions=[process_document]
    on_startup=startup
    on_shutdown=shutdown
    redis_settings=REDIS_SETTINGS