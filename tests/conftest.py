import os
import pytest

# Force SQLite for lifespan metadata creation during tests
os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.database import Base, get_db
import app.cache

# Setup SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Mock Redis Client
class MockRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, time, value):
        self.store[key] = value

    def delete(self, key):
        if key in self.store:
            del self.store[key]

    def clear(self):
        self.store.clear()


@pytest.fixture(scope="session", autouse=True)
def setup_mock_redis():
    mock_redis = MockRedis()
    app.cache.redis_client = mock_redis
    yield mock_redis
    app.cache.redis_client = None


@pytest.fixture(name="db")
def db_fixture():
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up database
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def client_fixture(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
