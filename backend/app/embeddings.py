
from sentence_transformers import SentenceTransformer
from app.database import SessionLocal
from sqlalchemy import text
import asyncio

def load_embedding_model():
    """
    Loads the embedding model for vector search
    """
    model=SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return model