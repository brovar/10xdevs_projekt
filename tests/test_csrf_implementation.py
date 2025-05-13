import logging
from uuid import UUID
from datetime import datetime, timezone

import pytest
from fastapi import status
from fastapi_csrf_protect import CsrfProtect
from starlette.testclient import TestClient

import dependencies
from main import app
from schemas import UserDTO, UserRole, UserStatus, UserListResponse

client = TestClient(app)


class SuccessCsrfProtect:
    """CSRF Protector that always succeeds validation."""

    def validate_csrf(self, request):
        pass  # Always validate successfully

    def set_csrf_cookie(self, response):
        pass  # No need to actually set a cookie for tests


class FailingCsrfProtect:
    """CSRF Protector that always fails validation."""

    def validate_csrf(self, request):
        # Always fail with a CSRF error
        from fastapi_csrf_protect.exceptions import CsrfProtectError

        raise CsrfProtectError("CSRF token missing or invalid")

    def set_csrf_cookie(self, response):
        pass  # No need to actually set a cookie for tests


def mock_authenticated_user():
    """Returns a mock authenticated user (basic)."""
    return {
        "user_id": "11111111-1111-1111-1111-111111111111",
        "email": "user@example.com",
        "role": "Buyer",
    }


def mock_authenticated_admin():
    """Returns a mock authenticated admin user."""
    return {
        "user_id": "22222222-2222-2222-2222-222222222222",
        "email": "admin@example.com",
        "role": "Admin",
    }


def mock_authenticated_seller():
    """Returns a mock authenticated seller user."""
    return {
        "user_id": "33333333-3333-3333-3333-333333333333",
        "email": "seller@example.com",
        "role": "Seller",
    }


def mock_admin_dto():
    """Returns a mock admin UserDTO."""
    return UserDTO(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        email="admin@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        first_name="Admin",
        last_name="User",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def mock_seller_dto():
    """Returns a mock seller UserDTO."""
    return UserDTO(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        email="seller@example.com",
        role=UserRole.SELLER,
        status=UserStatus.ACTIVE,
        first_name="Seller",
        last_name="User",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def mock_buyer_dto():
    """Returns a mock buyer UserDTO."""
    return UserDTO(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        email="user@example.com",
        role=UserRole.BUYER,
        status=UserStatus.ACTIVE,
        first_name="John",
        last_name="Doe",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def mock_require_admin():
    """Returns a mock admin user for require_admin dependency."""
    return mock_admin_dto()


def mock_require_seller():
    """Returns a mock seller user for require_seller dependency."""
    return mock_seller_dto()


def mock_require_buyer():
    """Returns a mock buyer user for require_buyer_or_seller dependency."""
    return mock_buyer_dto()


def mock_get_admin_user():
    """Returns a mock admin user for the get_admin_user dependency."""
    return mock_admin_dto()


@pytest.fixture
def setup_auth():
    """Set up authentication for tests."""
    # Store original overrides to restore later
    original_overrides = app.dependency_overrides.copy()

    # Mock all authentication dependencies
    for dep, mock_fn in [
        (dependencies.require_authenticated, mock_authenticated_user),
        (dependencies.require_admin, mock_require_admin),
        (dependencies.require_seller, mock_require_seller),
        (dependencies.require_buyer_or_seller, mock_require_buyer),
        (dependencies.get_admin_user, mock_get_admin_user),
    ]:
        app.dependency_overrides[dep] = lambda fn=mock_fn: fn()

    yield

    # Restore original overrides
    app.dependency_overrides = original_overrides
    for dep in [
        dependencies.require_authenticated,
        dependencies.require_admin,
        dependencies.require_seller,
        dependencies.require_buyer_or_seller,
        dependencies.get_admin_user,
    ]:
        if dep not in original_overrides:
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
        "quantity": 10,
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
        "quantity": 10,
    }
    response = client.post("/offers", data=data)
    # The actual response may vary, but not 403 with CSRF error
    assert (
        response.status_code != status.HTTP_403_FORBIDDEN
        or "CSRF" not in str(response.json())
    )


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
    assert (
        response.status_code != status.HTTP_403_FORBIDDEN
        or "CSRF" not in str(response.json())
    )


def test_change_password_csrf_failure(failing_csrf):
    """Test CSRF validation failure in change password endpoint."""
    response = client.put(
        "/account/password",
        json={
            "current_password": "OldPass123!",
            "new_password": "NewPass456!",
        },
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error_code"] == "INVALID_CSRF"
    assert "CSRF token missing or invalid" in data["detail"]["message"]


def test_change_password_csrf_success(success_csrf):
    """Test CSRF validation success in change password endpoint."""
    response = client.put(
        "/account/password",
        json={
            "current_password": "OldPass123!",
            "new_password": "NewPass456!",
        },
    )
    # The actual response may vary, but not 403 with CSRF error
    assert (
        response.status_code != status.HTTP_403_FORBIDDEN
        or "CSRF" not in str(response.json())
    )


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
    assert (
        response.status_code != status.HTTP_403_FORBIDDEN
        or "CSRF" not in str(response.json())
    )


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


# Stub UserService
class StubUserService:
    def __init__(self, db_session, logger):
        self.db_session = db_session
        self.logger = logger
    
    async def get_user_by_id(self, user_id):
        """Returns a mock user"""
        return UserDTO(
            id=user_id,
            email="test@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            first_name="Test",
            last_name="User"
        )
    
    async def block_user(self, user_id):
        """Mock blocking a user"""
        return UserDTO(
            id=user_id,
            email="test@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.INACTIVE,
            first_name="Test",
            last_name="User"
        )
    
    async def unblock_user(self, user_id):
        """Mock unblocking a user"""
        return UserDTO(
            id=user_id,
            email="test@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            first_name="Test",
            last_name="User"
        )
    
    async def list_users(self, page=1, limit=10, role=None, status=None, search=None):
        """Mock listing users"""
        mock_users = [
            UserDTO(
                id=UUID("11111111-1111-1111-1111-111111111111"),
                email="user@example.com",
                role=UserRole.BUYER,
                status=UserStatus.ACTIVE,
                first_name="John",
                last_name="Doe",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]
        
        return UserListResponse(
            items=mock_users,
            total=len(mock_users),
            page=page,
            limit=limit,
            pages=1,
        )

# Set up the dependency overrides
app.dependency_overrides[dependencies.get_user_service] = lambda: StubUserService(None, logging.getLogger("test")) 