import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models import User, GmailAccount, Email, EmailThread, Draft, StyleProfile, EmailChunk

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

from sqlalchemy.ext.compiler import compiles
from pgvector.sqlalchemy import Vector

@compiles(Vector, 'sqlite')
def compile_vector_sqlite(type_, compiler, **kw):
    return "TEXT"

from sqlalchemy.pool import StaticPool

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed a test user and a linked account since our API endpoints hardcode user_id=1 for MVP
    test_user = User(id=1, email="test@example.com", name="Test User")
    db.add(test_user)
    db.commit()
    
    test_account = GmailAccount(
        id=1,
        user_id=1,
        email_address="test@example.com",
        access_token="fake_token",
        refresh_token="fake_refresh",
        token_uri="fake_uri",
        client_id="fake_client",
        client_secret="fake_secret"
    )
    db.add(test_account)
    db.commit()
    
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after testing
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db_session):
    # Dependency override
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
