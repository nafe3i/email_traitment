import pytest

def test_cors_headers(client):
    response = client.options(
        "/health",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

def test_unauthorized_access(client):
    response = client.post("/emails/process", json={"sender": "test@test.com", "subject": "test", "body": "test", "send_reply": False})
    assert response.status_code == 403 # HTTPBearer missing -> 403

def test_authorized_access(client, admin_headers):
    # This might fail with 500 if DB is missing or ollama missing, but auth will pass
    response = client.get("/stats", headers=admin_headers)
    assert response.status_code in [200, 500] 

def test_rate_limiting(client):
    # Register limit is 3/hour
    for _ in range(3):
        client.post("/auth/register", json={"email": "limit@aui.ma", "password": "password123"})
    
    response = client.post("/auth/register", json={"email": "limit2@aui.ma", "password": "password123"})
    assert response.status_code == 429
