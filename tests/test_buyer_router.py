"""
Unit tests for the endpoints in the buyer_router.py module.

This test suite covers the following endpoints:
- GET /buyer/profile: get_buyer_profile
- GET /buyer/orders/history: get_order_history

The tests verify:
- Role-based access controls
- Success scenarios (correct status code and response body)
- Error handling (mapping service exceptions to HTTP errors 401, 403, 500)
- Dependency injection errors

Test Structure:
- Uses FastAPI's TestClient
- Mocks dependencies (database, logger)
- Uses pytest fixtures for setup and mocking authenticated users
"""

import pytest
from starlette.testclient import TestClient
from fastapi import status, HTTPException, Depends, Request
from typing import Dict, Optional, List, Any
from uuid import uuid4, UUID
import logging
import types

import dependencies
import routers.buyer_router as buyer_router
from main import app
from schemas import UserRole

# Mock user IDs and other constants
MOCK_BUYER_ID = uuid4()
MOCK_SELLER_ID = uuid4()
MOCK_ADMIN_ID = uuid4()

# Default authenticated user stubs
def _authenticated_buyer():
    return {
        'user_id': str(MOCK_BUYER_ID),
        'email': "buyer@example.com",
        'role': UserRole.BUYER
    }

def _authenticated_seller():
    return {
        'user_id': str(MOCK_SELLER_ID),
        'email': "seller@example.com",
        'role': UserRole.SELLER
    }

def _authenticated_admin():
    return {
        'user_id': str(MOCK_ADMIN_ID),
        'email': "admin@example.com",
        'role': UserRole.ADMIN
    }

# Mock CSRF Protection class
class MockCsrfProtect:
    async def validate_csrf_in_cookies(self, request: Request):
        pass

# Mock DB session
def mock_db_session_add(*args, **kwargs):
    pass

async def mock_db_session_commit(*args, **kwargs):
    pass

async def mock_db_session_rollback(*args, **kwargs):
    pass

mock_session = types.SimpleNamespace(
    add=mock_db_session_add,
    commit=mock_db_session_commit,
    rollback=mock_db_session_rollback
)

# Add logger to router
logger = logging.getLogger('test_buyer')
buyer_router.logger = logger

# Include the router for testing
app.include_router(buyer_router.router)

# Set up test client
client = TestClient(app)

@pytest.fixture(autouse=True)
def override_dependencies():
    """Fixture patching dependencies and services."""
    # Store current overrides to restore
    original_overrides = app.dependency_overrides.copy()

    # Mock User Management (local state within fixture)
    current_user_data = _authenticated_buyer()  # Default to buyer for these tests

    # Define Mock for require_buyer_or_seller Dependency
    async def mock_require_buyer_or_seller():
        if not current_user_data:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail={"error_code": "NOT_AUTHENTICATED", "message": "Użytkownik nie jest zalogowany."}
            )

        # Check if the user has the correct role
        if current_user_data['role'] not in [UserRole.BUYER, UserRole.SELLER]:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Nie masz uprawnień do wykonania tej operacji."}
            )

        return {
            "user_id": UUID(current_user_data['user_id']),
            "user_role": current_user_data['role'],
            "email": current_user_data['email']
        }

    # Override Dependencies
    app.dependency_overrides[dependencies.get_db_session] = lambda: mock_session
    app.dependency_overrides[dependencies.get_logger] = lambda: logger
    app.dependency_overrides[dependencies.require_buyer_or_seller] = mock_require_buyer_or_seller

    # Helper to change user for tests
    def set_mock_user(user_func):
        nonlocal current_user_data
        current_user_data = user_func() if user_func else None

    # Attach helper to the fixture function object for tests to use
    override_dependencies.set_mock_user = set_mock_user

    yield

    # Cleanup
    app.dependency_overrides = original_overrides
    if dependencies.get_db_session not in app.dependency_overrides:
        app.dependency_overrides[dependencies.get_db_session] = lambda: mock_session
    if dependencies.get_logger not in app.dependency_overrides:
        app.dependency_overrides[dependencies.get_logger] = lambda: logger

# Fixtures using the set_mock_user helper
@pytest.fixture
def seller_auth():
     override_dependencies.set_mock_user(_authenticated_seller)

@pytest.fixture
def admin_auth():
     override_dependencies.set_mock_user(_authenticated_admin)
     
@pytest.fixture
def no_auth():
     override_dependencies.set_mock_user(None)

# === Test GET /buyer/profile ===

def test_get_buyer_profile_success_as_buyer():
    """Test successful retrieval of buyer profile as a buyer."""
    # Default auth is buyer
    response = client.get("/buyer/profile")

    # Expect 200 OK
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Check response structure and content
    assert data["buyer_id"] == str(MOCK_BUYER_ID)
    assert data["role"] == UserRole.BUYER
    assert data["account_status"] == "active"
    assert "orders" in data
    assert "total" in data["orders"]
    assert "pending" in data["orders"]
    assert "completed" in data["orders"]

def test_get_buyer_profile_success_as_seller(seller_auth):
    """Test successful retrieval of buyer profile as a seller."""
    response = client.get("/buyer/profile")

    # Expect 200 OK
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Check response structure and content
    assert data["buyer_id"] == str(MOCK_SELLER_ID)
    assert data["role"] == UserRole.SELLER
    assert data["account_status"] == "active"
    assert "orders" in data

def test_get_buyer_profile_unauthorized(no_auth):
    """Test unauthorized access to buyer profile."""
    response = client.get("/buyer/profile")

    # Expect 401 UNAUTHORIZED
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail']['error_code'] == "NOT_AUTHENTICATED"

def test_get_buyer_profile_admin_forbidden(admin_auth):
    """Test forbidden access to buyer profile for admin users."""
    response = client.get("/buyer/profile")

    # Expect 403 FORBIDDEN
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()['detail']['error_code'] == "INSUFFICIENT_PERMISSIONS"

def test_get_buyer_profile_dependency_error():
    """Test handling of dependency injection errors."""
    # Override the require_buyer_or_seller dependency to simulate an error
    original_dependency = app.dependency_overrides[dependencies.require_buyer_or_seller]
    
    async def failing_dependency():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DEPENDENCY_ERROR", "message": "Simulated dependency error"}
        )
    
    app.dependency_overrides[dependencies.require_buyer_or_seller] = failing_dependency
    
    try:
        response = client.get("/buyer/profile")
        
        # Expect 500 INTERNAL SERVER ERROR
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"]["error_code"] == "DEPENDENCY_ERROR"
        assert "Simulated dependency error" in data["detail"]["message"]
    finally:
        # Restore the original dependency
        app.dependency_overrides[dependencies.require_buyer_or_seller] = original_dependency

# === Test GET /buyer/orders/history ===

def test_get_order_history_success_as_buyer():
    """Test successful retrieval of order history as a buyer."""
    # Default auth is buyer
    response = client.get("/buyer/orders/history")

    # Expect 200 OK
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Check response structure
    assert "orders" in data
    assert "total_orders" in data
    assert "total_spent" in data
    assert "most_recent_order" in data

def test_get_order_history_success_as_seller(seller_auth):
    """Test successful retrieval of order history as a seller."""
    response = client.get("/buyer/orders/history")

    # Expect 200 OK
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # Check response structure
    assert "orders" in data
    assert "total_orders" in data
    assert "total_spent" in data
    assert "most_recent_order" in data

def test_get_order_history_unauthorized(no_auth):
    """Test unauthorized access to order history."""
    response = client.get("/buyer/orders/history")

    # Expect 401 UNAUTHORIZED
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['detail']['error_code'] == "NOT_AUTHENTICATED"

def test_get_order_history_admin_forbidden(admin_auth):
    """Test forbidden access to order history for admin users."""
    response = client.get("/buyer/orders/history")

    # Expect 403 FORBIDDEN
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()['detail']['error_code'] == "INSUFFICIENT_PERMISSIONS"

def test_get_order_history_dependency_error():
    """Test handling of dependency injection errors."""
    # Override the require_buyer_or_seller dependency to simulate an error
    original_dependency = app.dependency_overrides[dependencies.require_buyer_or_seller]
    
    async def failing_dependency():
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "DEPENDENCY_ERROR", "message": "Simulated dependency error"}
        )
    
    app.dependency_overrides[dependencies.require_buyer_or_seller] = failing_dependency
    
    try:
        response = client.get("/buyer/orders/history")
        
        # Expect 500 INTERNAL SERVER ERROR
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"]["error_code"] == "DEPENDENCY_ERROR"
        assert "Simulated dependency error" in data["detail"]["message"]
    finally:
        # Restore the original dependency
        app.dependency_overrides[dependencies.require_buyer_or_seller] = original_dependency 