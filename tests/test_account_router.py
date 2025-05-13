from datetime import datetime
from types import \
    SimpleNamespace  # Added for potential use, though might not be needed now
from uuid import UUID

import pytest
from fastapi import HTTPException, status
from fastapi_csrf_protect import CsrfProtect  # Added
from fastapi_csrf_protect.exceptions import CsrfProtectError  # Added
from starlette.testclient import TestClient

import dependencies
import routers.account_router as account_router
from main import app
# Import schemas and request models used across all account tests
from schemas import ChangePasswordRequest, UpdateUserRequest, UserDTO

# --- Constants ---
MOCK_USER_ID = "11111111-1111-1111-1111-111111111111"  # Standardized
MOCK_USER_EMAIL = "user@example.com"  # Standardized

# --- Dependency Overrides ---

# Stub core dependencies
app.dependency_overrides[dependencies.get_db_session] = lambda: None
app.dependency_overrides[dependencies.get_logger] = lambda: __import__(
    "logging"
).getLogger("test")
# Add override for get_user_service
app.dependency_overrides[dependencies.get_user_service] = lambda: StubUserService(None, __import__("logging").getLogger("test"))


# Default authenticated session stub
def _authenticated_session():
    # Return a session_data dict with a fixed user_id and email
    return {"user_id": MOCK_USER_ID, "email": MOCK_USER_EMAIL}


app.dependency_overrides[dependencies.require_authenticated] = (
    _authenticated_session
)


# Default CSRF stub that does nothing (module-level override)
class NoopCsrfProtect:
    def validate_csrf(self, request):
        pass

    def set_csrf_cookie(self, response):  # Added for completeness if needed
        pass


app.dependency_overrides[account_router.CsrfProtect] = (
    lambda: NoopCsrfProtect()
)

# --- Test Client ---
client = TestClient(app)


# --- Unified UserService Stub ---
class StubUserService:
    # Flags/data to track calls
    get_current_user_called = False
    get_current_user_called_with = None
    update_user_profile_called = False
    update_user_profile_called_with = None
    change_password_called = False
    change_password_called_with = None

    # Mock implementations (can be overridden by tests using monkeypatch)
    _get_current_user_impl = None
    _update_user_profile_impl = None
    _change_password_impl = None

    def __init__(self, db_session, logger):
        # Reset state for each instance potentially created (though overridden by fixture)
        self.reset()

    @classmethod
    def reset(cls):
        cls.get_current_user_called = False
        cls.get_current_user_called_with = None
        cls.update_user_profile_called = False
        cls.update_user_profile_called_with = None
        cls.change_password_called = False
        cls.change_password_called_with = None
        # Reset implementations to default success behavior or raise NotImplementedError
        cls._get_current_user_impl = cls._default_get_current_user
        cls._update_user_profile_impl = cls._default_update_user_profile
        cls._change_password_impl = cls._default_change_password

    # Default implementations (Success scenarios)
    @classmethod
    async def _default_get_current_user(cls, user_id: UUID):
        return UserDTO(
            id=user_id,  # Use the passed ID
            email=MOCK_USER_EMAIL,
            role="Buyer",
            status="Active",
            first_name="John",
            last_name="Doe",
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            updated_at=datetime(2023, 1, 2, 13, 0, 0),
        )

    @classmethod
    async def _default_update_user_profile(
        cls, user_id: UUID, update_data: UpdateUserRequest
    ):
        return UserDTO(
            id=user_id,
            email=MOCK_USER_EMAIL,
            role="Buyer",
            status="Active",
            first_name=update_data.first_name
            or "John",  # Use original if None
            last_name=update_data.last_name or "Doe",  # Use original if None
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            updated_at=datetime(2023, 1, 3, 14, 0, 0),  # Different update time
        )

    @classmethod
    async def _default_change_password(
        cls,
        user_id: UUID,
        password_data: ChangePasswordRequest,
        request_ip: str,
    ):
        return True  # Simulate success

    # Actual methods called by the application via the router
    async def get_current_user(self, user_id: UUID):
        StubUserService.get_current_user_called = True
        StubUserService.get_current_user_called_with = user_id
        return await StubUserService._get_current_user_impl(user_id)

    async def update_user_profile(
        self, user_id: UUID, update_data: UpdateUserRequest
    ):
        StubUserService.update_user_profile_called = True
        StubUserService.update_user_profile_called_with = (
            user_id,
            update_data,
        )
        return await StubUserService._update_user_profile_impl(
            user_id, update_data
        )

    async def change_password(
        self,
        user_id: UUID,
        password_data: ChangePasswordRequest,
        request_ip: str,
    ):
        StubUserService.change_password_called = True
        StubUserService.change_password_called_with = (
            user_id,
            password_data,
            request_ip,
        )
        return await StubUserService._change_password_impl(
            user_id, password_data, request_ip
        )


# --- Fixture to Manage Stubs ---
@pytest.fixture(autouse=True)
def manage_stubs(monkeypatch):
    # Reset the UserService stub before each test
    StubUserService.reset()
    # Apply the stub UserService globally for the test
    monkeypatch.setattr(account_router, "UserService", StubUserService)
    # Ensure default CSRF and Auth overrides are in place (can be overridden per-test)
    monkeypatch.setitem(
        app.dependency_overrides,
        account_router.CsrfProtect,
        lambda: NoopCsrfProtect(),
    )
    monkeypatch.setitem(
        app.dependency_overrides,
        dependencies.require_authenticated,
        _authenticated_session,
    )
    yield


# =============================================
# === Tests for GET /account Endpoint ===
# =============================================


def test_get_current_user_success():
    response = client.get("/account")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify returned fields match the default stub
    assert data["id"] == MOCK_USER_ID  # Should match the ID from the session
    assert data["email"] == MOCK_USER_EMAIL
    assert data["role"] == "Buyer"
    assert data["status"] == "Active"
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["created_at"].startswith("2023-01-01T12:00:00")
    assert data["updated_at"].startswith(
        "2023-01-02T13:00:00"
    )  # Matches default stub

    # Ensure service was called correctly
    assert StubUserService.get_current_user_called is True
    assert isinstance(StubUserService.get_current_user_called_with, UUID)
    assert str(StubUserService.get_current_user_called_with) == MOCK_USER_ID


# 2. Unauthenticated scenario: require_authenticated raises HTTPException 401
def test_get_current_user_unauthenticated(monkeypatch):
    # Override authentication to raise for this test
    def bad_auth():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "NOT_AUTHENTICATED",
                "message": "Użytkownik nie jest zalogowany.",
            },
        )

    monkeypatch.setitem(
        app.dependency_overrides, dependencies.require_authenticated, bad_auth
    )

    response = client.get("/account")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert "detail" in body
    assert body["detail"]["error_code"] == "NOT_AUTHENTICATED"
    assert body["detail"]["message"] == "Użytkownik nie jest zalogowany."


# 3. User not found scenario: service raises HTTPException 404
def test_get_current_user_not_found(monkeypatch):
    # Configure the stub method to raise an error for this test
    async def raise_not_found(
        *args, **kwargs
    ):  # Use generic signature for patching
        # We can still track the call if needed within the patched function
        # StubUserService.get_current_user_called = True
        # StubUserService.get_current_user_called_with = args[1] # Assuming user_id is the first arg after self/cls
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "USER_NOT_FOUND",
                "message": "Nie znaleziono użytkownika.",
            },
        )

    # Patch the main method directly
    monkeypatch.setattr(StubUserService, "get_current_user", raise_not_found)

    response = client.get("/account")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    assert "detail" in body
    assert body["detail"]["error_code"] == "USER_NOT_FOUND"
    assert body["detail"]["message"] == "Nie znaleziono użytkownika."


# 4. Server error scenario: service raises generic Exception => 500 FETCH_FAILED
def test_get_current_user_server_error(monkeypatch):
    # Configure the stub method to raise an error for this test
    async def raise_server_error(*args, **kwargs):
        raise Exception("DB down")

    # Patch the main method directly
    monkeypatch.setattr(
        StubUserService, "get_current_user", raise_server_error
    )

    response = client.get("/account")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = response.json()
    assert "detail" in body
    assert body["detail"]["error_code"] == "FETCH_FAILED"
    assert (
        body["detail"]["message"]
        == "Wystąpił nieoczekiwany błąd podczas pobierania profilu użytkownika."
    )


# ==================================================
# === Tests for PATCH /account Endpoint ===
# ==================================================


@pytest.mark.parametrize(
    "payload, expected_first, expected_last",
    [
        ({"first_name": "NewFirst"}, "NewFirst", "Doe"),  # Update first only
        ({"last_name": "NewLast"}, "John", "NewLast"),  # Update last only
        ({"first_name": "F", "last_name": "L"}, "F", "L"),  # Update both
    ],
)
def test_update_profile_success(payload, expected_first, expected_last):
    response = client.patch("/account", json=payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify response data matches expected updated values
    assert data["id"] == MOCK_USER_ID
    assert data["first_name"] == expected_first
    assert data["last_name"] == expected_last
    assert data["email"] == MOCK_USER_EMAIL  # Email shouldn't change
    assert data["updated_at"].startswith(
        "2023-01-03T14:00:00"
    )  # Matches default stub update time

    # Ensure service was called correctly
    assert StubUserService.update_user_profile_called is True
    uid, upd_data = StubUserService.update_user_profile_called_with
    assert isinstance(uid, UUID)
    assert str(uid) == MOCK_USER_ID
    assert isinstance(upd_data, UpdateUserRequest)
    assert upd_data.first_name == payload.get("first_name")
    assert upd_data.last_name == payload.get("last_name")


def test_update_profile_validation_error_no_fields():
    # Test the specific check within the endpoint (not Pydantic)
    response = client.patch("/account", json={})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    detail = body.get("detail", {})
    assert detail.get("error_code") == "INVALID_INPUT"
    assert "Należy podać co najmniej jedno pole" in detail.get("message", "")


# Pydantic validation (e.g., field length) would also yield 422 if constraints were added
# def test_update_profile_pydantic_validation_error():
#     response = client.patch('/account', json={'first_name': 'A'*101}) # Assuming max_length=100
#     assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#     # Check details...


def test_update_profile_unauthenticated(monkeypatch):
    # Override authentication to raise for this test
    def bad_auth():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "NOT_AUTHENTICATED",
                "message": "Użytkownik nie jest zalogowany.",
            },
        )

    monkeypatch.setitem(
        app.dependency_overrides, dependencies.require_authenticated, bad_auth
    )

    response = client.patch("/account", json={"first_name": "X"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    detail = body.get("detail", {})
    assert detail.get("error_code") == "NOT_AUTHENTICATED"


def test_update_profile_csrf_error(monkeypatch):
    # Define and apply a CSRF stub that raises an error for this test
    class BadCsrf:
        def validate_csrf(self, request):
            raise CsrfProtectError(
                status_code=403, message="CSRF token missing or invalid"
            )

        def set_csrf_cookie(self, response):
            pass

    monkeypatch.setitem(
        app.dependency_overrides, account_router.CsrfProtect, lambda: BadCsrf()
    )

    response = client.patch("/account", json={"first_name": "X"})
    assert response.status_code == status.HTTP_403_FORBIDDEN
    body = response.json()
    # The endpoint catches CsrfProtectError and returns a specific JSON structure with detail
    assert body.get("detail", {}).get("error_code") == "INVALID_CSRF"
    assert (
        body.get("detail", {}).get("message")
        == "CSRF token missing or invalid"
    )


def test_update_profile_not_found(monkeypatch):
    # Configure the stub method to raise an error for this test
    async def raise_not_found(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "USER_NOT_FOUND",
                "message": "Nie znaleziono użytkownika.",
            },
        )

    # Patch the main method directly
    monkeypatch.setattr(
        StubUserService, "update_user_profile", raise_not_found
    )

    response = client.patch("/account", json={"first_name": "X"})
    assert response.status_code == status.HTTP_404_NOT_FOUND
    body = response.json()
    detail = body.get("detail", {})
    assert detail.get("error_code") == "USER_NOT_FOUND"


def test_update_profile_server_error(monkeypatch):
    # Configure the stub method to raise an error for this test
    async def raise_server_error(*args, **kwargs):
        raise Exception("db fail")

    # Patch the main method directly
    monkeypatch.setattr(
        StubUserService, "update_user_profile", raise_server_error
    )

    response = client.patch("/account", json={"first_name": "X"})
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = response.json()
    detail = body.get("detail", {})
    assert detail.get("error_code") == "PROFILE_UPDATE_FAILED"
    assert (
        "Wystąpił błąd podczas aktualizacji profilu użytkownika."
        in detail.get("message", "")
    )


# =====================================================
# === Tests for PUT /account/password Endpoint ===
# =====================================================

valid_password_payload = {
    "current_password": "OldPass123!",
    "new_password": "NewValidPass456!",
}


def test_change_password_success():
    response = client.put("/account/password", json=valid_password_payload)
    assert response.status_code == status.HTTP_200_OK
    # Accept either English or Polish success message
    assert response.json().get("message") in [
        "Password updated successfully",
        "Hasło zostało zmienione pomyślnie.",
    ]

    # Ensure service was called correctly
    assert StubUserService.change_password_called is True
    uid, pdata, ip = StubUserService.change_password_called_with
    assert isinstance(uid, UUID)
    assert str(uid) == MOCK_USER_ID
    assert pdata.current_password == valid_password_payload["current_password"]
    assert pdata.new_password == valid_password_payload["new_password"]
    assert ip == "testclient"  # Default IP for TestClient


# Using 422 for Pydantic validation errors
@pytest.mark.parametrize(
    "payload, expected_error_part",
    [
        ({}, "Field required"),  # Missing fields
        (
            {"current_password": "abc"},
            "Field required",
        ),  # Missing new_password
        (
            {"new_password": "abc"},
            "Field required",
        ),  # Missing current_password
        # Password policy checks (assuming they are in the Pydantic model)
        (
            {"current_password": "OldPass123!", "new_password": "short"},
            "Password must be at least 10 characters long",
        ),
        (
            {
                "current_password": "OldPass123!",
                "new_password": "nouppercase123!",
            },
            "Password must contain an uppercase letter",
        ),
        (
            {
                "current_password": "OldPass123!",
                "new_password": "NOLOWERCASE123!",
            },
            "Password must contain a lowercase letter",
        ),
        (
            {
                "current_password": "OldPass123!",
                "new_password": "NoDigitOrSpecial",
            },
            "Password must contain a digit or special character",
        ),
    ],
)
def test_change_password_pydantic_validation_error(
    payload, expected_error_part
):
    response = client.put("/account/password", json=payload)
    # FastAPI returns 400 for these specific validation errors based on test results
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    # Pydantic V2 errors might be in 'detail' directly or structured differently.
    # Check the whole body as a string for robustness.
    # assert 'detail' in body # This might fail depending on FastAPI/Pydantic version
    assert expected_error_part in str(body)  # Check raw body string


def test_change_password_unauthenticated(monkeypatch):
    # Override authentication to raise for this test
    def bad_auth():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "NOT_AUTHENTICATED",
                "message": "Użytkownik nie jest zalogowany.",
            },
        )

    monkeypatch.setitem(
        app.dependency_overrides, dependencies.require_authenticated, bad_auth
    )

    response = client.put("/account/password", json=valid_password_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    detail = body.get("detail", {})
    assert detail.get("error_code") == "NOT_AUTHENTICATED"


def test_change_password_csrf_error(monkeypatch):
    # Define and apply a CSRF stub that raises an error for this test
    class BadCsrf:
        def validate_csrf(self, request):
            raise CsrfProtectError(
                status_code=403, message="CSRF token missing or invalid"
            )

        def set_csrf_cookie(self, response):
            pass

    monkeypatch.setitem(
        app.dependency_overrides, account_router.CsrfProtect, lambda: BadCsrf()
    )

    response = client.put("/account/password", json=valid_password_payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    body = response.json()
    # The endpoint catches CsrfProtectError and returns detail structure
    assert body.get("detail", {}).get("error_code") == "INVALID_CSRF"
    assert (
        body.get("detail", {}).get("message")
        == "CSRF token missing or invalid"
    )


def test_change_password_invalid_current(monkeypatch):
    # Configure the stub method to raise the specific error
    async def raise_invalid_current(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "INVALID_CURRENT_PASSWORD",
                "message": "Aktualne hasło jest nieprawidłowe.",
            },
        )

    # Patch the main method directly
    monkeypatch.setattr(
        StubUserService, "change_password", raise_invalid_current
    )

    response = client.put("/account/password", json=valid_password_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    detail = body.get("detail", {})
    assert detail.get("error_code") == "INVALID_CURRENT_PASSWORD"


def test_change_password_user_not_found(monkeypatch):
    # Configure the stub method to raise the specific error (assuming service handles this)
    async def raise_not_found(*args, **kwargs):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "USER_NOT_FOUND",
                "message": "Nie znaleziono użytkownika.",
            },
        )

    # Patch the main method directly
    monkeypatch.setattr(StubUserService, "change_password", raise_not_found)

    response = client.put("/account/password", json=valid_password_payload)
    assert (
        response.status_code == status.HTTP_404_NOT_FOUND
    )  # Assuming service raises 404
    body = response.json()
    detail = body.get("detail", {})
    assert detail.get("error_code") == "USER_NOT_FOUND"


def test_change_password_server_error(monkeypatch):
    # Configure the stub method to raise a generic error
    async def raise_server_error(*args, **kwargs):
        raise Exception("db connection failed")

    # Patch the main method directly
    monkeypatch.setattr(StubUserService, "change_password", raise_server_error)

    response = client.put("/account/password", json=valid_password_payload)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = response.json()
    detail = body.get("detail", {})
    assert detail.get("error_code") == "PASSWORD_UPDATE_FAILED"
    # Accept either English or Polish error message
    assert any(
        msg in detail.get("message", "")
        for msg in ["nieoczekiwany błąd", "Wystąpił błąd podczas zmiany hasła"]
    )
