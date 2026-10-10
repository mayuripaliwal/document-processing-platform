from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL=os.environ["DATABASE_URL"]
ENVIRONMENT=os.environ["ENVIRONMENT"]

IS_PRODUCTION=True if ENVIRONMENT=="production" else False

engine=create_async_engine(DATABASE_URL,echo=False if IS_PRODUCTION else True)

SessionLocal=async_sessionmaker(autocommit=False,autoflush=False,bind=engine)

class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as db:
        yield db