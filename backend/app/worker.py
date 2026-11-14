# Background worker for processing an uploaded document
from arq.connections import RedisSettings
from docling.document_converter import DocumentConverter
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
from docling_core.types.doc import DocItemLabel
from app.storage import ObjectStorage, IFileStorage, LocalStorage
from typing import BinaryIO
import boto3
import os
from dotenv import load_dotenv
from docling.datamodel.base_models import DocumentStream
from fastapi import FastAPI
from arq.worker import create_worker
from contextlib import asynccontextmanager

load_dotenv()

REDIS_URL=os.environ["REDIS_URL"]

logger=logging.getLogger(__name__)

if sys.platform=="win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

MAX_JOB_TRIES=3

@asynccontextmanager
async def lifespan(app: FastAPI):
    # start the worker
    worker=create_worker(
        WorkerSettings,
        poll_delay=10,
        health_check_interval=300
    )
    app.state.worker_task=asyncio.create_task(
        worker.async_run()
    )
    try:
        yield
    finally:
        app.state.worker_task.cancel()

        try:
            await app.state.worker_task
        except asyncio.CancelledError:
            pass
        finally:
            await worker.close()

app=FastAPI(lifespan=lifespan)

@app.get('/')
async def home():
    return {
        "status":"ok"
    }

async def extract_document_storage_key(document_id:int)->str | None:
    """
    - Extracts the document storage_key for a given document ID from db
    - Returns None if document does not exist
    """
    async with SessionLocal() as db:
        result=await db.execute(select(Document.stored_file_name).where(Document.id==document_id))
        storage_key=result.scalar_one_or_none()

        if storage_key is None:
            return None
        
        return storage_key

def extract_text(file:BinaryIO, ctx)->list[LangchainDocument]:
    """
    Returns a list of LangchainDocument objects with text and metadata from the given PDF file.
    """
    doc=ctx["document_converter"].convert(DocumentStream(
        name="document.pdf",
        stream=file
    )).document

    current_section=None
    documents=[]

    for item, level in doc.iterate_items():
        if item.label==DocItemLabel.TABLE:
            print("Table:")
            print(item.export_to_markdown(doc=doc))
            
        if item.label==DocItemLabel.SECTION_HEADER:
            current_section=item.text
            continue

        elif item.label == DocItemLabel.TEXT:
            text=item.text

        elif item.label==DocItemLabel.LIST_ITEM:
            text=f"- {item.text}"

        elif item.label==DocItemLabel.TABLE:
            text=item.export_to_markdown(doc=doc) # we extract the table as markdown
        else:
            continue

        if not text or not text.strip() or not item.prov:
            continue

        documents.append(LangchainDocument(
            page_content=text,
            metadata={
                "page_no":item.prov[0].page_no,
                "section_title":current_section
            }
        ))

    return documents

async def save_document_text(document_id:int, extracted_text:str):
    """
    - Stores extracted text in documents
    """
    async with SessionLocal() as db:
        await db.execute(update(Document).where(Document.id==document_id, Document.extracted_text.is_(None)).values(extracted_text=extracted_text))

        await db.commit()

def chunk_text(documents:list[LangchainDocument])->list[dict]:
    """
    Returns a list of text chunks with maximum chunk size 800
    """
    CHUNK_SIZE=800

    CHUNK_OVERLAP=80

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    chunks=text_splitter.split_documents(documents)

    result=[]

    for chunk in chunks:
        result.append({
            "text":chunk.page_content,
            "page_no":chunk.metadata['page_no'],
            "section_title":chunk.metadata['section_title']
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
                "section_title":chunk["section_title"]
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
        # 1. Extract storage_key of the document from DB
        try:
            storage_key=await extract_document_storage_key(document_id)
            logger.info("Extracted storage_key for document_id: %s", document_id)
        except Exception:
            logger.exception("Failed to extract storage_key for document_id: %s", document_id)
            raise

        if storage_key is None:
            # document does not exist, means it got deleted after it was added 
            # and before worker could process it
            logger.info("storage_key does not exist for document_id: %s", document_id)
            return 

        # 2. Retrieve file from file storage

        try:
            file=await asyncio.to_thread(ctx["file_storage"].get, storage_key)

            if file is None:
                logger.error("File not found for document_id: %s", document_id)
                return 
        except ValueError:
            logger.exception("Found invalid storage_key for document_id: %s in DB", document_id)
            raise

        # 3. Update document status
                
        await updateDocumentStatus(
            document_id,
            DocumentStatus.PROCESSING
        )
        
        # 4. Extract text and metadata from file for each page
        
        try:
            extracted_documents=await asyncio.to_thread(extract_text,file, ctx)
        except Exception:
            logger.exception("Failed to extract text for document_id: %s", document_id)
            raise
        finally:
            file.close()

        # 5. Extract text from the extracted_documents
        
        extracted_text=[]
        for document in extracted_documents:
            extracted_text.append(document.page_content)

        extracted_text="\n\n".join(extracted_text)

        logger.info("Extracted text for document_id: %s", document_id)

        # 6. Save extracted text in DB
        
        try:
            await save_document_text(document_id, extracted_text)
        except Exception:
            logger.exception("Failed to save extracted text for document_id: %s", document_id)
            raise

        logger.info("Saved extracted text for document_id: %s", document_id)

        # 7. Extract chunks each containing text and metadata from extracted_documents
        
        try:
            chunks=await asyncio.to_thread(chunk_text,extracted_documents)
        except Exception:
            logger.exception("Failed to extract chunks for document_id: %s", document_id)
            raise

        logger.info("Extracted chunks for document_id: %s", document_id)

        model=ctx["embedding_model"]

        # 8. Extract text from each chunk
        
        chunk_texts=[]
        for chunk in chunks:
            chunk_texts.append(chunk["text"])

        # 9. Generate embeddings for each chunk text
        
        try:
            logger.info("Extracting embeddings for document_id: %s", document_id)
            embeddings=await asyncio.to_thread(lambda:list(model.embed(chunk_texts)))
            embeddings=[embedding.tolist() for embedding in embeddings]
        except Exception:
            logger.exception("Failed to extract embeddings for document_id: %s", document_id)
            raise

        logger.info("Extracted embeddings for document_id: %s", document_id)

        # 10. Save chunks and embeddings in DB
        
        try:
            await save_document_chunk_details(document_id,chunks, embeddings)
        except Exception:
            logger.exception("Failed to save chunks and embeddings for document_id: %s", document_id)
            raise

        # 11. Update document status to COMPLETED
        
        await updateDocumentStatus(
            document_id,
            DocumentStatus.COMPLETED
        )

        logger.info("Saved chunks and embeddings for document_id: %s", document_id)

    except asyncio.CancelledError:
        logger.exception("Processing failed for document_id=%s, attempt=%s", document_id, ctx["job_try"])
        raise

    except Exception:
        logger.exception("Processing failed for document_id=%s, attempt=%s", document_id, ctx["job_try"])
        if ctx["job_try"]==MAX_JOB_TRIES:
            await updateDocumentStatus(
                document_id,
                DocumentStatus.FAILED
            )
        raise


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

    # s3_client for ObjectStorage
    s3_client=boto3.client(
        "s3",
        endpoint_url=os.environ["SUPABASE_S3_ENDPOINT"],
        region_name=os.environ["SUPABASE_S3_REGION"],
        aws_access_key_id=os.environ["SUPABASE_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["SUPABASE_SECRET_ACCESS_KEY"]
    )

    ctx["s3_client"]=s3_client

    ctx["file_storage"]=ObjectStorage(s3_client)
    
    
async def shutdown(ctx):
    s3_client=ctx.get("s3_client")

    s3_client.close()

    logger.info("Stopped ARQ Worker")

class WorkerSettings:
    functions=[process_document]
    on_startup=startup
    on_shutdown=shutdown
    redis_settings=RedisSettings.from_dsn(
        REDIS_URL
    )
    job_timeout = 10 * 60
    max_tries=MAX_JOB_TRIES