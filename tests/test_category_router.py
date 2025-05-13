from typing import List
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from starlette.testclient import TestClient

import dependencies
import routers.category_router as category_router
from main import app
# Import schema for type checking and response validation
from schemas import CategoryDTO, LogEventType, UserDTO, UserRole, UserStatus

# Stub core dependencies
app.dependency_overrides[dependencies.get_db_session] = lambda: None
app.dependency_overrides[dependencies.get_logger] = lambda: __import__(
    "logging"
).getLogger("test")

# Mock user ID for authenticated requests
MOCK_USER_ID = uuid4()
MOCK_USER_EMAIL = "test@example.com"


# Default authenticated user stub
def _authenticated_user():
    # Return a dictionary matching how session_data is used in the router
    return {"user_id": str(MOCK_USER_ID), "email": MOCK_USER_EMAIL}


app.dependency_overrides[dependencies.require_authenticated] = (
    lambda: _authenticated_user()
)

client = TestClient(app)


# Stub CategoryService
class StubCategoryService:
    called = False

    def __init__(
        self, db_session=None, logger=None
    ):  # Match potential dependency injection
        pass

    async def list_categories(self) -> List[CategoryDTO]:
        StubCategoryService.called = True
        # Simulate successful retrieval
        return [
            CategoryDTO(id=1, name="Electronics"),
            CategoryDTO(id=2, name="Books"),
        ]

    async def get_all_categories(self) -> List[CategoryDTO]:
        StubCategoryService.called = True
        # Simulate successful retrieval
        return [
            CategoryDTO(id=1, name="Electronics"),
            CategoryDTO(id=2, name="Books"),
        ]


# Stub LogService
class StubLogService:
    create_log_called = False
    create_log_data = None

    def __init__(self, db_session=None, logger=None):
        pass

    async def create_log(
        self, event_type, message, user_id=None, ip_address=None
    ):
        StubLogService.create_log_called = True
        StubLogService.create_log_data = {
            "user_id": user_id,
            "event_type": event_type,
            "message": message,
            "ip_address": ip_address,
        }

    # Stare metody pozostawione dla zachowania kompatybilności z istniejącymi testami
    async def log_event(self, user_id, event_type, message):
        return await self.create_log(
            event_type=event_type, message=message, user_id=user_id
        )

    async def log_error(self, error_message, endpoint, user_id=None):
        return await self.create_log(
            event_type="ERROR",
            message=f"Error in {endpoint}: {error_message}",
            user_id=user_id,
        )


# Add Stub UserService class
class StubUserService:
    def __init__(self, db_session, logger):
        self.db_session = db_session
        self.logger = logger
    
    async def get_user_by_id(self, user_id):
        """Returns a mock user based on ID"""
        return UserDTO(
            id=user_id,
            email="test@example.com",
            role=UserRole.ADMIN,  # Default to admin for tests
            status=UserStatus.ACTIVE,
            first_name="Test",
            last_name="User"
        )


@pytest.fixture(autouse=True)
def override_services(monkeypatch):
    # Reset stub states
    StubCategoryService.called = False
    StubLogService.create_log_called = False
    StubLogService.create_log_data = None

    # Apply overrides
    monkeypatch.setattr(
        category_router, "CategoryService", StubCategoryService
    )
    monkeypatch.setattr(category_router, "LogService", StubLogService)
    
    # Fix: Override the dependency function directly instead of trying to override its return value
    app.dependency_overrides[dependencies.get_user_service] = lambda: StubUserService(None, __import__("logging").getLogger("test"))
    yield


# 1. Success scenario
def test_list_categories_success():
    response = client.get("/categories")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "items" in body
    assert len(body["items"]) == 2
    assert body["items"][0] == {"id": 1, "name": "Electronics"}
    assert body["items"][1] == {"id": 2, "name": "Books"}

    # Verify service call
    assert StubCategoryService.called is True
    
    # Verify anonymous logging is called
    assert StubLogService.create_log_called is True
    assert StubLogService.create_log_data["user_id"] is None  # Anonymous user
    assert StubLogService.create_log_data["event_type"] == LogEventType.CATEGORY_LIST_VIEWED


# 2. Unauthenticated scenario - now should succeed since we removed authentication requirement
def test_list_categories_unauthenticated(monkeypatch):
    # Override authentication to raise
    def bad_auth():
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "NOT_AUTHENTICATED",
                "message": "Authentication required",
            },
        )

    monkeypatch.setitem(
        app.dependency_overrides, dependencies.require_authenticated, bad_auth
    )

    # Request should now succeed since we don't require authentication
    response = client.get("/categories")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "items" in body
    assert len(body["items"]) == 2


# 3. Service error scenario
def test_list_categories_service_error(monkeypatch):
    # Mock CategoryService to raise an error
    class ErrorCategoryService(StubCategoryService):
        async def list_categories(self) -> List[CategoryDTO]:
            raise Exception("Database connection failed")
            
        async def get_all_categories(self) -> List[CategoryDTO]:
            raise Exception("Database connection failed")

    monkeypatch.setattr(
        category_router, "CategoryService", ErrorCategoryService
    )

    response = client.get("/categories")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = response.json()
    assert body.get("detail", {}).get("error_code") == "FETCH_FAILED"
    assert (
        body.get("detail", {}).get("message")
        == "Failed to retrieve category data"
    )

    # Verify error logging is no longer done through LogService
    assert not StubLogService.create_log_called


# End of originally intended tests for this file, removing hallucinated tests below.
