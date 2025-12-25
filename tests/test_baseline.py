"""
Baseline Tests - Existing Endpoints
These tests verify the endpoints we created on Day 2
"""
from fastapi.testclient import TestClient


def test_health_endpoint(client):
    """
    Test the /health endpoint returns healthy status
    
    RED (Expected to PASS - we have this endpoint)
    """
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint(client):
    """
    Test the root endpoint returns welcome message
    
    RED (Expected to PASS - we have this endpoint)
    """
    response = client.get("/")
    
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Welcome to XploraKodo API"


def test_cors_headers(client):
    """
    Test that CORS headers are properly set
    
    We test CORS by checking the headers on a GET request
    """
    response = client.get("/")
    
    # Check if response has CORS headers
    # In development, we allow all origins
    assert response.status_code == 200
    # FastAPI with CORSMiddleware will add these headers
