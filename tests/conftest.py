import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Must set env before loading settings in api
os.environ["SECRET_KEY"] = "test_fernet_key_must_be_at_least_32_bytes_long_"
os.environ["JWT_SECRET"] = "test_jwt_secret_must_be_at_least_32_bytes_long_"
os.environ["ENVIRONMENT"] = "testing"

from api import app
from database import Base, get_db, create_user, get_user_by_email
from auth import hash_password, create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user(db):
    user = get_user_by_email(db, "admin@test.com")
    if not user:
        user = create_user(db, "admin@test.com", hash_password("password123"), "admin")
    return user

@pytest.fixture
def normal_user(db):
    user = get_user_by_email(db, "user@test.com")
    if not user:
        user = create_user(db, "user@test.com", hash_password("password123"), "viewer")
    return user

@pytest.fixture
def admin_token(admin_user):
    return create_access_token({"user_id": admin_user.id, "email": admin_user.email, "role": "admin"})

@pytest.fixture
def user_token(normal_user):
    return create_access_token({"user_id": normal_user.id, "email": normal_user.email, "role": "viewer"})

@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}
