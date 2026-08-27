import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# A fresh in-memory SQLite database for the whole test run. StaticPool keeps
# every connection pointed at the same in-memory database — without it,
# SQLite's default pooling would hand out a *new*, empty in-memory database
# per connection, and tables created in one request wouldn't be visible in
# the next.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Every route depends on get_db via Depends(get_db). This swaps that
# dependency out app-wide for the test database, the same way you'd swap it
# in production for a different real database.
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_database():
    """Give every test a clean set of tables, so tests can't see each other's data."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Register + log in a fresh user, returning headers ready to use on any protected route."""
    client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpass123", "full_name": "Test User"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def categories(client, auth_headers):
    """The 6 default categories auto-seeded on registration, keyed by name."""
    response = client.get("/categories/", headers=auth_headers)
    return {c["name"]: c for c in response.json()}
