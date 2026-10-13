from app.database import Base
from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, func, Enum as SQLEnum, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from enum import Enum

class Document(Base):
    """
    Schema for defining a document object
    {`id`, `user_id`, `file_name`, `stored_file_name`, `mime_type`, `file_size`, `storage_path`, `created_at`, `extracted_text`}
    """
    __tablename__="documents"

    id:Mapped[int]=mapped_column(BigInteger,primary_key=True,autoincrement=True)
    user_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("users.id"),nullable=False)
    file_name:Mapped[str]=mapped_column(String(255),nullable=False)
    stored_file_name:Mapped[str]=mapped_column(String(255),nullable=False, unique=True)
    mime_type:Mapped[str]=mapped_column(String(100),nullable=False)
    file_size:Mapped[int]=mapped_column(BigInteger, nullable=False)
    storage_path:Mapped[str]=mapped_column(Text, nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    extracted_text:Mapped[str|None]=mapped_column(Text, nullable=True)

class User(Base):
    """
    Schema for defining a user object
    """
    __tablename__="users"

    id:Mapped[int]=mapped_column(BigInteger, primary_key=True,autoincrement=True)
    email:Mapped[str]=mapped_column(String(255),nullable=False,unique=True)
    password_hash:Mapped[str]=mapped_column(String(255),nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)

class DocumentChunk(Base):
    """
    Schema for defining a document chunk
    {`id`, `document_id`, `chunk_index`, `content`}
    """
    __tablename__="document_chunks"

    __table_args__=(
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="unique_document_id_chunk_index"
        ),
    )

    id:Mapped[int]=mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id:Mapped[int]=mapped_column(BigInteger, ForeignKey("documents.id"),nullable=False)
    chunk_index:Mapped[int]=mapped_column(Integer, nullable=False)
    content:Mapped[str]=mapped_column(Text, nullable=False)