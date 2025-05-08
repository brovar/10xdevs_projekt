import pytest
from starlette.testclient import TestClient
from fastapi import status, HTTPException
from typing import List
from uuid import uuid4

import dependencies
import routers.category_router as category_router
from main import app

# Import schema for type checking and response validation
from schemas import CategoryDTO, CategoriesListResponse

# Stub core dependencies
app.dependency_overrides[dependencies.get_db_session] = lambda: None
app.dependency_overrides[dependencies.get_logger] = lambda: __import__('logging').getLogger('test')

# Mock user ID for authenticated requests
MOCK_USER_ID = uuid4()
MOCK_USER_EMAIL = "test@example.com"

# Default authenticated user stub
def _authenticated_user():
    # Return a dictionary matching how session_data is used in the router
    return {'user_id': str(MOCK_USER_ID), 'email': MOCK_USER_EMAIL}
app.dependency_overrides[dependencies.require_authenticated] = lambda: _authenticated_user()

client = TestClient(app)

# Stub CategoryService
class StubCategoryService:
    called = False

    def __init__(self, db_session=None, logger=None): # Match potential dependency injection
        pass

    async def get_all_categories(self) -> List[CategoryDTO]:
        StubCategoryService.called = True
        # Simulate successful retrieval
        return [
            CategoryDTO(id=1, name="Electronics"),
            CategoryDTO(id=2, name="Books")
        ]

# Stub LogService
class StubLogService:
    log_event_called = False
    log_error_called = False
    log_event_data = None
    log_error_data = None
    
    def __init__(self, db_session=None, logger=None):
        pass

    async def log_event(self, user_id, event_type, message):
        StubLogService.log_event_called = True
        StubLogService.log_event_data = {'user_id': user_id, 'event_type': event_type, 'message': message}
    
    async def log_error(self, error_message, endpoint, user_id=None):
        StubLogService.log_error_called = True
        StubLogService.log_error_data = {'error_message': error_message, 'endpoint': endpoint, 'user_id': user_id}

@pytest.fixture(autouse=True)
def override_services(monkeypatch):
    # Reset stub states
    StubCategoryService.called = False
    StubLogService.log_event_called = False
    StubLogService.log_error_called = False
    StubLogService.log_event_data = None
    StubLogService.log_error_data = None
    
    # Apply overrides
    monkeypatch.setattr(category_router, 'CategoryService', StubCategoryService)
    monkeypatch.setattr(category_router, 'LogService', StubLogService)
    yield

# 1. Success scenario
def test_list_categories_success():
    response = client.get("/categories")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert 'items' in body
    assert len(body['items']) == 2
    assert body['items'][0] == {'id': 1, 'name': 'Electronics'}
    assert body['items'][1] == {'id': 2, 'name': 'Books'}
    
    # Verify service and logging calls
    assert StubCategoryService.called is True
    assert StubLogService.log_event_called is True
    assert str(StubLogService.log_event_data['user_id']) == str(MOCK_USER_ID) # Compare as strings
    assert StubLogService.log_event_data['event_type'] == "CATEGORY_LIST_VIEWED"
    assert StubLogService.log_error_called is False

# 2. Unauthenticated scenario
def test_list_categories_unauthenticated(monkeypatch):
    # Override authentication to raise
    def bad_auth():
        raise HTTPException(status_code=401, detail={'error_code': 'NOT_AUTHENTICATED', 'message': 'Authentication required'})
    monkeypatch.setitem(app.dependency_overrides, dependencies.require_authenticated, bad_auth)
    
    response = client.get("/categories")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    body = response.json()
    assert body.get('detail', {}).get('error_code') == 'NOT_AUTHENTICATED'

# 3. Service error scenario
def test_list_categories_service_error(monkeypatch):
    # Mock CategoryService to raise an error
    class ErrorCategoryService(StubCategoryService):
        async def get_all_categories(self) -> List[CategoryDTO]:
            raise Exception("Database connection failed")
    monkeypatch.setattr(category_router, 'CategoryService', ErrorCategoryService)
    
    response = client.get("/categories")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body = response.json()
    assert body.get('detail', {}).get('error_code') == 'FETCH_FAILED'
    assert body.get('detail', {}).get('message') == 'Failed to retrieve category data'
    
    # Verify error logging
    assert StubLogService.log_error_called is True
    assert str(StubLogService.log_error_data['user_id']) == str(MOCK_USER_ID) # Compare as strings
    assert StubLogService.log_error_data['endpoint'] == '/categories'
    assert "Database connection failed" in StubLogService.log_error_data['error_message']
    assert StubLogService.log_event_called is False 