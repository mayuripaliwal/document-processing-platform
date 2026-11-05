from arq.connections import RedisSettings
from docling.document_converter import DocumentConverter
from pathlib import Path
from app.database import SessionLocal
from app.models import Document, DocumentChunk, DocumentStatus
from sqlalchemy import select, update, text
from sqlalchemy.dialects.postgresql import insert
import asyncio
import sys
from app.embeddings import load_embedding_model
import logging
from langchain_core.documents import Document as LangchainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger=logging.getLogger(__name__)

if sys.platform=="win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

REDIS_SETTINGS=RedisSettings(
    host="127.0.0.1",
    port=6379
)

MAX_JOB_TRIES=3

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

def extract_text(file:Path, ctx)->list[dict]:
    """
    Returns a dict for each page with page_no and text from the given PDF file.
    """
    doc=ctx["document_converter"].convert(file).document

    pages=[]

    page_nos=sorted(doc.pages.keys())

    print(f"page_nos: {page_nos}")

    for page_no in page_nos:
        markdown=doc.export_to_markdown(page_no=page_no).strip()

        if markdown:
            pages.append({
                "page_no":page_no,
                "text":markdown
            })

    return pages

async def save_document_text(document_id:int, extracted_text:str):
    """
    - Stores extracted text in documents
    """
    async with SessionLocal() as db:
        await db.execute(update(Document).where(Document.id==document_id, Document.extracted_text.is_(None)).values(extracted_text=extracted_text))

        await db.commit()

def chunk_text(pages:list[dict])->list[dict]:
    """
    Returns a list of text chunks with maximum chunk size 200
    """
    CHUNK_SIZE=200

    CHUNK_OVERLAP=50

    langchain_documents=[]

    #page number and content
    for page in pages:
        langchain_documents.append(LangchainDocument(page_content=page["text"], 
            metadata={"page_no":page["page_no"]}
        ))


    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    chunks=[]
    
    chunks=text_splitter.split_documents(langchain_documents)

    result=[]

    for chunk in chunks:
        result.append({
            "text":chunk.page_content,
            "page_no":chunk.metadata['page_no']
        })

    return result

async def save_document_chunk_details(document_id:int,chunks:list[dict], embeddings:list[list[float]]):
    """
    Stores document chunk details[chunk, embedding] of a given document id in document_chunks
    """

    document_chunk_details=[]
    for chunk_index, (chunk,embedding) in enumerate(zip(chunks, embeddings)):
        document_chunk_details.append(
            {
                "document_id":document_id,
                "chunk_index":chunk_index,
                "content":chunk["text"],
                "embedding":embedding,
                "page_no":chunk["page_no"],
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
    try:
        try:
            storage_path=await extract_document_storage_path(document_id)
            logger.info("Extracted storage path for document_id: %s", document_id)
        except Exception:
            logger.exception("Failed to extract storage path for document_id: %s", document_id)
            raise

        if storage_path is None:
            #document does not exist, means it got deleted after it was added 
            # and before worker could process it
            logger.info("Storage path does not exist for document_id: %s", document_id)
            return

        await updateDocumentStatus(
            document_id,
            DocumentStatus.PROCESSING
        )
        try:
            extracted_pages=await asyncio.to_thread(extract_text,storage_path, ctx)
        except Exception:
            logger.exception("Failed to extract text for document_id: %s", document_id)
            raise
        extracted_pages_text=[]
        for page in extracted_pages:
            extracted_pages_text.append(page["text"])

        extracted_text="\n\n".join(extracted_pages_text)
        if not extracted_text.strip():
            return

        logger.info("Extracted text for document_id: %s", document_id)

        try:
            await save_document_text(document_id, extracted_text)
        except Exception:
            logger.exception("Failed to save extracted text for document_id: %s", document_id)
            raise

        logger.info("Saved extracted text for document_id: %s", document_id)

        #store chunks and their embeddings
        
        try:
            chunks=await asyncio.to_thread(chunk_text,extracted_pages)
        except Exception:
            logger.exception("Failed to extract chunks for document_id: %s", document_id)
            raise

        logger.info("Extracted chunks for document_id: %s", document_id)

        model=ctx["embedding_model"]

        chunk_texts=[]
        for chunk in chunks:
            chunk_texts.append(chunk["text"])

        try:
            logger.info("Extracting embeddings for document_id: %s", document_id)
            embeddings=await asyncio.to_thread(model.encode, chunk_texts)
        except Exception:
            logger.exception("Failed to extract embeddings for document_id: %s", document_id)
            raise

        logger.info("Extracted embeddings for document_id: %s", document_id)

        try:
            await save_document_chunk_details(document_id,chunks, embeddings.tolist())
        except Exception:
            logger.exception("Failed to save chunks and embeddings for document_id: %s", document_id)
            raise

        await updateDocumentStatus(
            document_id,
            DocumentStatus.COMPLETED
        )

        logger.info("Saved chunks and embeddings for document_id: %s", document_id)
    except asyncio.CancelledError:
        logger.exception("Processing failed for document_id=%s, attempt=%s", document_id, ctx["job_try"])
        await updateDocumentStatus(
            document_id,
            DocumentStatus.FAILED
        )


async def updateDocumentStatus(document_id:int, status:DocumentStatus):
    """Updates document status to provided status in db
    """
    async with SessionLocal() as db:
        await db.execute(text("""
        UPDATE Documents 
        SET document_status=:status 
        WHERE id=:id 
        """),{
            "id":document_id,
            "status":status
        })
        await db.commit()

async def startup(ctx):
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s %(funcName)s: %(message)s",level=logging.INFO)
    
    logger.info("Started ARQ Worker")
    
    ctx["embedding_model"]=load_embedding_model()

    logger.info("Embedding model loaded")

    ctx["document_converter"]=DocumentConverter()

    logger.info("Document converter loaded")
    
    
async def shutdown(ctx):
    logger.info("Stopped ARQ Worker")
    pass

class WorkerSettings:
    functions=[process_document]
    on_startup=startup
    on_shutdown=shutdown
    redis_settings=REDIS_SETTINGS
    job_timeout = 10 * 60
    max_tries=MAX_JOB_TRIES