import pytest
from src.auth import hash_password, verify_password

def test_password_hashing():
    pwd = "password123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong", hashed) is False

def test_register_user(client):
    response = client.post("/auth/register", json={"email": "new@aui.ma", "password": "password123"})
    assert response.status_code == 200
    assert response.json()["email"] == "new@aui.ma"

def test_register_invalid(client):
    response = client.post("/auth/register", json={"email": "invalid", "password": "pass"})
    assert response.status_code == 422 # Pydantic validation error

def test_login_user(client, normal_user):
    response = client.post("/auth/login", json={"email": "user@test.com", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(client, normal_user):
    response = client.post("/auth/login", json={"email": "user@test.com", "password": "wrong"})
    assert response.status_code == 401
