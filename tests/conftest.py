import os
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_workspace.db"
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-validation"
os.environ["ENVIRONMENT"] = "test"

import app.models  # noqa: E402,F401
from app.config.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_DB = Path("test_workspace.db")
engine = create_async_engine(os.environ["DATABASE_URL"])
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_db():
    async with Session() as session:
        yield session


app.dependency_overrides[get_db] = override_db


@pytest_asyncio.fixture(autouse=True)
async def database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http
