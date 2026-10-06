from app.database import Base
from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from enum import Enum

class DocumentStatus(Enum):
    """
    Enum for document status stages.
    """
    UPLOADED="UPLOADED"
    PROCESSING="PROCESSING"
    COMPLETED="COMPLETED"
    FAILED="FAILED"

class Document(Base):
    """
    Schema for defining a document object
    """
    __tablename__="documents"

    id:Mapped[int]=mapped_column(BigInteger,primary_key=True,autoincrement=True)
    user_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("users.id"),nullable=False)
    file_name:Mapped[str]=mapped_column(String(255),nullable=False)
    stored_file_name:Mapped[str]=mapped_column(String(255),nullable=False, unique=True)
    mime_type:Mapped[str]=mapped_column(String(100),nullable=False)
    file_size:Mapped[int]=mapped_column(BigInteger, nullable=False)
    storage_path:Mapped[str]=mapped_column(Text, nullable=False)
    document_status:Mapped[DocumentStatus]=mapped_column(SQLEnum(DocumentStatus,name="document_status"),nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)

class User(Base):
    """
    Schema for defining a user object
    """
    __tablename__="users"

    id:Mapped[int]=mapped_column(BigInteger, primary_key=True,autoincrement=True)
    email:Mapped[str]=mapped_column(String(255),nullable=False,unique=True)
    password_hash:Mapped[str]=mapped_column(String(255),nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)