from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, async_sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL=os.environ["DATABASE_URL"]

engine=create_async_engine(DATABASE_URL,echo=True)

SessionLocal=async_sessionmaker(autocommit=False,autoflush=False,bind=engine)

class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as db:
        yield db