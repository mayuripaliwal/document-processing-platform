from database import Base
from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class Document(Base):
    __tablename__="documents"

    id:Mapped[int]=mapped_column(BigInteger,primary_key=True,autoincrement=True)
    user_id:Mapped[int]=mapped_column(BigInteger,ForeignKey("users.id"),nullable=False)
    file_name:Mapped[str]=mapped_column(String(255),nullable=False)
    stored_file_name:Mapped[str]=mapped_column(String(255),nullable=False, unique=True)
    mime_type:Mapped[str]=mapped_column(String(100),nullable=False)
    file_size:Mapped[int]=mapped_column(BigInteger, nullable=False)
    storage_path:Mapped[str]=mapped_column(Text, nullable=False)
    status:Mapped[str]=mapped_column(String(30),nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True,server_default=func.now()),nullable=False)
