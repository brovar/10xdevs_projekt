"""
Unit tests for the CSRF protection implementation in the application.

These tests verify that the CSRF validation works consistently across all routers
after changing from validate_csrf_in_cookies to validate_csrf.
"""

import pytest
from starlette.testclient import TestClient
from fastapi import status, Request, Response
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from uuid import uuid4, UUID
import logging
from types import SimpleNamespace

from main import app
import dependencies
from schemas import UserRole, UserDTO

# --- Constants ---
MOCK_USER_ID = UUID('11111111-1111-1111-1111-111111111111')
MOCK_ADMIN_ID = UUID('22222222-2222-2222-2222-222222222222')
MOCK_SELLER_ID = UUID('33333333-3333-3333-3333-333333333333')

# --- Mock classes for CSRF protection ---

class SuccessCsrfProtect:
    """Mock CSRF protector that does nothing (simulates success)."""
    def validate_csrf(self, request):
        pass
    
    def set_csrf_cookie(self, response):
        pass

class FailingCsrfProtect:
    """Mock CSRF protector that raises an error (simulates CSRF failure)."""
    def validate_csrf(self, request):
        raise CsrfProtectError(status_code=403, message="CSRF token missing or invalid")
    
    def set_csrf_cookie(self, response):
        pass

# --- Mock authentication functions ---

def mock_authenticated_user():
    """Mock of an authenticated regular user."""
    return {
        'user_id': MOCK_USER_ID,
        'email': 'user@example.com',
        'role': UserRole.BUYER
    }

def mock_authenticated_admin():
    """Mock of an authenticated admin user for authentication middleware."""
    return {
        'user_id': MOCK_ADMIN_ID,
        'email': 'admin@example.com',
        'role': UserRole.ADMIN
    }

def mock_authenticated_seller():
    """Mock of an authenticated seller."""
    return {
        'user_id': MOCK_SELLER_ID,
        'email': 'seller@example.com',
        'role': UserRole.SELLER
    }

# User DTO objects for endpoints requiring structured user objects
def mock_admin_dto():
    """Mock admin user as UserDTO object."""
    admin = UserDTO(
        id=MOCK_ADMIN_ID,
        email='admin@example.com',
        role=UserRole.ADMIN,
        status='Active',
        first_name='Admin',
        last_name='User',
        created_at='2025-01-01T00:00:00Z',
        updated_at='2025-01-01T00:00:00Z'
    )
    return admin

def mock_seller_dto():
    """Mock seller user as UserDTO object."""
    seller = UserDTO(
        id=MOCK_SELLER_ID,
        email='seller@example.com',
        role=UserRole.SELLER,
        status='Active',
        first_name='Seller',
        last_name='User',
        created_at='2025-01-01T00:00:00Z',
        updated_at='2025-01-01T00:00:00Z'
    )
    return seller

def mock_buyer_dto():
    """Mock buyer user as UserDTO object."""
    buyer = UserDTO(
        id=MOCK_USER_ID,
        email='user@example.com',
        role=UserRole.BUYER,
        status='Active',
        first_name='Test',
        last_name='User',
        created_at='2025-01-01T00:00:00Z',
        updated_at='2025-01-01T00:00:00Z'
    )
    return buyer

def mock_require_admin():
    """Mock of require_admin dependency."""
    return mock_admin_dto()

def mock_require_seller():
    """Mock of require_seller dependency."""
    return mock_seller_dto()

def mock_require_buyer():
    """Mock of require_buyer dependency."""
    return mock_buyer_dto()

# --- Test client ---
client = TestClient(app)

# --- Test Fixtures ---
@pytest.fixture
def setup_auth():
    """Set up authentication dependencies."""
    original_overrides = {}
    
    # Store original overrides
    dependencies_to_override = [
        dependencies.require_authenticated, 
        dependencies.require_admin, 
        dependencies.require_seller,
        dependencies.require_roles
    ]
    
    for dep in dependencies_to_override:
        original_overrides[dep] = app.dependency_overrides.get(dep)
    
    # Override dependencies
    app.dependency_overrides[dependencies.require_authenticated] = lambda: mock_authenticated_user()
    app.dependency_overrides[dependencies.require_admin] = mock_require_admin
    app.dependency_overrides[dependencies.require_seller] = mock_require_seller
    
    # Handle require_roles dependency which takes arguments
    app.dependency_overrides[dependencies.require_roles] = lambda roles: mock_require_buyer
    
    yield
    
    # Restore original overrides
    for dep, override in original_overrides.items():
        if override:
            app.dependency_overrides[dep] = override
        else:
            app.dependency_overrides.pop(dep, None)

@pytest.fixture
def success_csrf(setup_auth):
    """Override CsrfProtect dependency to success implementation."""
    original_override = app.dependency_overrides.get(CsrfProtect)
    app.dependency_overrides[CsrfProtect] = lambda: SuccessCsrfProtect()
    yield
    if original_override:
        app.dependency_overrides[CsrfProtect] = original_override
    else:
        app.dependency_overrides.pop(CsrfProtect, None)

@pytest.fixture
def failing_csrf(setup_auth):
    """Override CsrfProtect dependency to failing implementation."""
    original_override = app.dependency_overrides.get(CsrfProtect)
    app.dependency_overrides[CsrfProtect] = lambda: FailingCsrfProtect()
    yield
    if original_override:
        app.dependency_overrides[CsrfProtect] = original_override
    else:
        app.dependency_overrides.pop(CsrfProtect, None)

# --- Tests for CSRF in Auth Router ---

# Note: Login and logout endpoints may check credentials before CSRF, so these tests may not be reliable
# We'll focus on the endpoints where we know CSRF is checked first

# --- Tests for CSRF in Offer Router ---

def test_create_offer_csrf_failure(failing_csrf):
    """Test CSRF validation failure in create offer endpoint."""
    data = {
        "title": "Test Offer",
        "price": "99.99",
        "category_id": 1,
        "quantity": 10
    }
    response = client.post("/offers", data=data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_code"] == "INVALID_CSRF"
    assert "CSRF token missing or invalid" in data["detail"]["message"]

def test_create_offer_csrf_success(success_csrf):
    """Test CSRF validation success in create offer endpoint."""
    data = {
        "title": "Test Offer",
        "price": "99.99",
        "category_id": 1,
        "quantity": 10
    }
    response = client.post("/offers", data=data)
    # The actual response may vary, but not 403 with CSRF error
    assert response.status_code != status.HTTP_403_FORBIDDEN or "CSRF" not in str(response.json())

# --- Tests for CSRF in Account Router ---

def test_update_profile_csrf_failure(failing_csrf):
    """Test CSRF validation failure in update profile endpoint."""
    response = client.patch("/account", json={"first_name": "New Name"})
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_code"] == "INVALID_CSRF"
    assert "CSRF token missing or invalid" in data["detail"]["message"]

def test_update_profile_csrf_success(success_csrf):
    """Test CSRF validation success in update profile endpoint."""
    response = client.patch("/account", json={"first_name": "New Name"})
    # The actual response may vary, but not 403 with CSRF error
    assert response.status_code != status.HTTP_403_FORBIDDEN or "CSRF" not in str(response.json())

def test_change_password_csrf_failure(failing_csrf):
    """Test CSRF validation failure in change password endpoint."""
    response = client.put("/account/password", 
                         json={"current_password": "OldPass123!", "new_password": "NewPass456!"})
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_code"] == "INVALID_CSRF"
    assert "CSRF token missing or invalid" in data["detail"]["message"]

def test_change_password_csrf_success(success_csrf):
    """Test CSRF validation success in change password endpoint."""
    response = client.put("/account/password", 
                         json={"current_password": "OldPass123!", "new_password": "NewPass456!"})
    # The actual response may vary, but not 403 with CSRF error
    assert response.status_code != status.HTTP_403_FORBIDDEN or "CSRF" not in str(response.json())

# --- Tests for CSRF in Admin Router ---

def test_block_user_csrf_failure(failing_csrf):
    """Test CSRF validation failure in block user endpoint."""
    user_id = "11111111-1111-1111-1111-111111111111"  # Dummy UUID
    response = client.post(f"/admin/users/{user_id}/block")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_code"] == "INVALID_CSRF"
    assert "CSRF token missing or invalid" in data["detail"]["message"]

def test_block_user_csrf_success(success_csrf):
    """Test CSRF validation success in block user endpoint."""
    user_id = "11111111-1111-1111-1111-111111111111"  # Dummy UUID
    response = client.post(f"/admin/users/{user_id}/block")
    # The actual response may vary, but not 403 with CSRF error
    assert response.status_code != status.HTTP_403_FORBIDDEN or "CSRF" not in str(response.json())

def test_refresh_csrf_token(setup_auth):
    """Test the new refresh CSRF token endpoint."""
    # Create a successful CSRF protector that properly sets cookies
    class WorkingCsrfProtect:
        def validate_csrf(self, request):
            pass
        
        def set_csrf_cookie(self, response):
            # Actually set a cookie
            response.set_cookie(key="fastapi-csrf-token", value="test_token")
    
    # Override CsrfProtect dependency
    original_override = app.dependency_overrides.get(CsrfProtect)
    app.dependency_overrides[CsrfProtect] = lambda: WorkingCsrfProtect()
    
    try:
        response = client.post("/auth/refresh-csrf")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "refreshed" in data["message"]
        
        # Check for cookie in response
        assert "fastapi-csrf-token" in response.cookies
    finally:
        # Restore original override
        if original_override:
            app.dependency_overrides[CsrfProtect] = original_override
        else:
            app.dependency_overrides.pop(CsrfProtect, None) 