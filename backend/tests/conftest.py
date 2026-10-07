import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.database import get_db
from app.main import app
import pytest
from fastapi.testclient import TestClient

TEST_DATABASE_URL=os.environ["TEST_DATABASE_URL"]

test_engine=create_async_engine(TEST_DATABASE_URL,echo=True)


TestSessionLocal=async_sessionmaker(bind=test_engine,autoflush=False)

async def override_get_db():
    async with TestSessionLocal() as db:
        yield db

@pytest.fixture
def client():
    """
    - Provides a test client `client`
    - Overrides `get_db` to `override_get_db` which provides a test db session
    """
    app.dependency_overrides[get_db]=override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
