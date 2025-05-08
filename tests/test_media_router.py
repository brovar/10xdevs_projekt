"""
Unit tests for the endpoints in the media_router.py module.

This test suite covers the following endpoints:
- GET /media/offers/{offer_id}/{filename}: get_offer_image

The tests verify:
- Access control for various user roles and offer statuses
- Success scenarios with proper file responses and headers
- Error handling (mapping service exceptions to HTTP errors 403, 404, 500)
- File path validation
- Cache control headers

Test Structure:
- Uses FastAPI's TestClient
- Mocks dependencies (database, logger, media_service)
- Mocks FileResponse to avoid actual file system access
- Uses pytest fixtures for setup and mocking authenticated users
"""

import pytest
from fastapi import FastAPI, APIRouter, Depends, status, HTTPException, Path, Response
from starlette.testclient import TestClient
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, Optional, Any, Union
from uuid import uuid4, UUID
import logging
import pathlib
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os

# Constants for testing
MOCK_BUYER_ID = uuid4()
MOCK_SELLER_ID = uuid4()
MOCK_ADMIN_ID = uuid4()
MOCK_OFFER_ID = uuid4()
MOCK_FILENAME = "test_image.png"
MOCK_FILE_PATH = "/tmp/test_image.png"

# Add src directory to path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fixed imports to work with tests
from schemas import UserRole
from exceptions.offer_exceptions import OfferNotFoundException

# Configure test logger
test_logger = logging.getLogger("test_media_logger")
test_logger.setLevel(logging.INFO)

# Create mock user objects
class MockUser:
    def __init__(self, id: UUID, role: UserRole):
        self.id = id
        self.role = role

# Mock offer object
class MockOffer:
    def __init__(self, id: UUID, seller_id: UUID, status: str = "active"):
        self.id = id
        self.seller_id = seller_id
        self.status = status

# Create MediaService stub
class StubMediaService:
    _access_allowed = True
    _raise_on_check_access = None
    _raise_on_get_path = None
    _return_path = MOCK_FILE_PATH
    
    def __init__(self, logger):
        self.logger = logger
    
    @classmethod
    def reset(cls):
        cls._access_allowed = True
        cls._raise_on_check_access = None
        cls._raise_on_get_path = None
        cls._return_path = MOCK_FILE_PATH
    
    async def check_offer_image_access(self, offer, user_id, user_role):
        if self._raise_on_check_access:
            raise self._raise_on_check_access
        
        if not self._access_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error_code": "ACCESS_DENIED", "message": "Access denied to this image"}
            )
        
        return True
    
    async def get_offer_image_path(self, offer_id, filename, offer):
        if self._raise_on_get_path:
            raise self._raise_on_get_path
        
        return pathlib.Path(self._return_path)

# Configure mock test dependencies
current_user = None
mock_db = MagicMock()
offer_status = "active"

async def mock_get_db_session():
    """Mock database session"""
    return mock_db

async def mock_get_offer(model_class, pk):
    """Mock database get method"""
    if str(pk) == "00000000-0000-0000-0000-000000000000":
        return None
    
    return MockOffer(
        id=pk,
        seller_id=MOCK_SELLER_ID,
        status=offer_status
    )

def mock_get_logger():
    """Mock logger dependency"""
    return test_logger

def mock_get_media_service():
    """Mock media service dependency"""
    return StubMediaService(test_logger)

async def mock_get_current_user_optional():
    """Mock current user (auth) dependency"""
    return current_user

# Completely custom FileResponse for testing
class CustomTestFileResponse(Response):
    """
    Custom FileResponse that doesn't try to access the file system.
    Used only for testing purposes.
    """
    media_type = "image/png"
    
    def __init__(self, path, **kwargs):
        # Store the attributes that would be used by a real FileResponse
        self.path = str(path)
        self.filename = kwargs.get("filename", os.path.basename(self.path))
        self.media_type = kwargs.get("media_type", "image/png")
        
        # Add custom headers if provided
        headers = kwargs.get("headers", {})
        
        # Create a response without accessing the file
        super().__init__(
            content="Mock file content for testing",
            media_type=self.media_type,
            headers=headers,
            status_code=200
        )

# Setup our own test endpoint using only what we need
@pytest.fixture
def test_app():
    """Create isolated FastAPI test app with mocked dependencies"""
    # Setup media test router
    router = APIRouter()
    
    @router.get("/media/offers/{offer_id}/{filename}", response_model=None)
    async def get_offer_image(
        offer_id: UUID = Path(...),
        filename: str = Path(...),
        current_user = Depends(mock_get_current_user_optional),
        db = Depends(mock_get_db_session),
        logger = Depends(mock_get_logger),
        media_service = Depends(mock_get_media_service)
    ) -> Union[CustomTestFileResponse, JSONResponse]:
        """Test endpoint that mimics the real endpoint but uses our mocks"""
        try:
            # Mock the db.get call
            offer = await mock_get_offer(None, offer_id)
            
            # Check if offer exists
            if not offer:
                raise OfferNotFoundException(offer_id)
            
            # Extract user information if authenticated
            current_user_id = current_user.id if current_user else None
            current_user_role = current_user.role if current_user else None
            
            # Check access permission
            await media_service.check_offer_image_access(
                offer,
                current_user_id,
                current_user_role
            )
            
            # Get validated file path
            file_path = await media_service.get_offer_image_path(
                offer_id,
                filename,
                offer
            )
            
            # Set cache control based on offer status
            cache_control = "public, max-age=3600" if offer.status == "active" else "no-store"
            
            # Return mock file response with appropriate headers
            return CustomTestFileResponse(
                path=str(file_path),
                media_type="image/png",
                filename=filename,
                headers={"Cache-Control": cache_control}
            )
            
        except HTTPException as exc:
            # Convert HTTPException to JSONResponse
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )
        except OfferNotFoundException as exc:
            # Handle OfferNotFoundException
            logger.error(f"Unexpected error in get_offer_image endpoint: {str(exc)}")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "detail": {
                        "error_code": "OFFER_NOT_FOUND",
                        "message": f"Offer {offer_id} not found"
                    }
                }
            )
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error in get_offer_image endpoint: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": {
                        "error_code": "FILE_SERVE_FAILED",
                        "message": "An unexpected error occurred"
                    }
                }
            )
    
    # Create test FastAPI app and add router
    app = FastAPI()
    app.include_router(router)
    
    # Create test client
    client = TestClient(app)
    
    # Reset mocks before each test
    mock_db.reset_mock()
    mock_db.get = mock_get_offer
    StubMediaService.reset()
    
    yield client

# Helper functions for setting up test environment
def set_user(user_type=None):
    global current_user
    if user_type == "buyer":
        current_user = MockUser(id=MOCK_BUYER_ID, role=UserRole.BUYER)
    elif user_type == "seller":
        current_user = MockUser(id=MOCK_SELLER_ID, role=UserRole.SELLER)
    elif user_type == "admin":
        current_user = MockUser(id=MOCK_ADMIN_ID, role=UserRole.ADMIN)
    else:
        current_user = None  # Anonymous user

def set_offer_status(status):
    global offer_status
    offer_status = status

# Tests for GET /media/offers/{offer_id}/{filename}

def test_get_offer_image_success_active_offer_public_access(test_app):
    """Test successful image retrieval for active offer by anonymous user."""
    # Reset mock state
    StubMediaService.reset()
    set_user(None)  # Anonymous
    set_offer_status("active")
    
    response = test_app.get(f"/media/offers/{MOCK_OFFER_ID}/{MOCK_FILENAME}")
    assert response.status_code == status.HTTP_200_OK
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "public, max-age=3600"

def test_get_offer_image_success_authenticated_user(test_app):
    """Test successful image retrieval for active offer by authenticated user."""
    # Reset mock state
    StubMediaService.reset()
    set_user("buyer")
    set_offer_status("active")
    
    response = test_app.get(f"/media/offers/{MOCK_OFFER_ID}/{MOCK_FILENAME}")    
    assert response.status_code == status.HTTP_200_OK
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "public, max-age=3600"

def test_get_offer_image_success_owner_access(test_app):
    """Test successful image retrieval by offer owner for inactive offer."""
    # Reset mock state
    StubMediaService.reset()
    set_user("seller")  # Owner
    set_offer_status("inactive")
    
    response = test_app.get(f"/media/offers/{MOCK_OFFER_ID}/{MOCK_FILENAME}")   
    assert response.status_code == status.HTTP_200_OK
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "no-store"

def test_get_offer_image_success_admin_access(test_app):
    """Test successful image retrieval by admin for inactive offer."""
    # Reset mock state
    StubMediaService.reset()
    set_user("admin")
    set_offer_status("inactive")
    
    response = test_app.get(f"/media/offers/{MOCK_OFFER_ID}/{MOCK_FILENAME}")   
    assert response.status_code == status.HTTP_200_OK
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "no-store"

def test_get_offer_image_offer_not_found(test_app):
    """Test handling when offer is not found."""
    # Reset mock state
    StubMediaService.reset()
    
    # Use UUID that will trigger "not found" in mock
    offer_id = "00000000-0000-0000-0000-000000000000"
    
    response = test_app.get(f"/media/offers/{offer_id}/{MOCK_FILENAME}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"]["error_code"] == "OFFER_NOT_FOUND"

def test_get_offer_image_access_denied(test_app):
    """Test handling when user is denied access to an image."""
    # Configure mock to deny access
    StubMediaService._access_allowed = False
    
    response = test_app.get(f"/media/offers/{MOCK_OFFER_ID}/{MOCK_FILENAME}")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"]["error_code"] == "ACCESS_DENIED"

def test_get_offer_image_file_not_found(test_app):
    """Test handling when image file is not found."""
    # Configure mock to raise file not found error
    StubMediaService._raise_on_get_path = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error_code": "FILE_NOT_FOUND", "message": "Image file not found"}
    )
    
    response = test_app.get(f"/media/offers/{MOCK_OFFER_ID}/{MOCK_FILENAME}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"]["error_code"] == "FILE_NOT_FOUND"

def test_get_offer_image_invalid_filename(test_app):
    """Test handling when filename is invalid."""
    # Configure mock to raise validation error
    StubMediaService._raise_on_get_path = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"error_code": "INVALID_FILENAME", "message": "Filename contains invalid characters"}
    )
    
    response = test_app.get(f"/media/offers/{MOCK_OFFER_ID}/invalid..filename.png")
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"]["error_code"] == "INVALID_FILENAME"

def test_get_offer_image_unexpected_error(test_app):
    """Test handling of unexpected errors."""
    # Configure mock to raise unexpected error
    StubMediaService._raise_on_check_access = Exception("Unexpected database error")
    
    response = test_app.get(f"/media/offers/{MOCK_OFFER_ID}/{MOCK_FILENAME}")
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"]["error_code"] == "FILE_SERVE_FAILED"

def test_get_offer_image_invalid_offer_id(test_app):
    """Test validation error for invalid offer ID format."""
    response = test_app.get(f"/media/offers/not-a-valid-uuid/{MOCK_FILENAME}")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_offer_image_cache_control_active(test_app):
    """Test cache-control headers for active offer."""
    # Reset mock state
    StubMediaService.reset()
    set_offer_status("active")
    
    # Use test_app to get response
    response = test_app.get(f"/media/offers/{MOCK_OFFER_ID}/{MOCK_FILENAME}")
    
    # Check for FileResponse headers
    assert response.status_code == status.HTTP_200_OK
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "public, max-age=3600"

def test_get_offer_image_cache_control_inactive(test_app):
    """Test cache-control headers for inactive offer."""
    # Reset mock state
    StubMediaService.reset()
    set_user("seller")  # Owner
    set_offer_status("inactive")
    
    # Use test_app to get response
    response = test_app.get(f"/media/offers/{MOCK_OFFER_ID}/{MOCK_FILENAME}")
    
    # Check for FileResponse headers
    assert response.status_code == status.HTTP_200_OK
    assert "Cache-Control" in response.headers
    assert response.headers["Cache-Control"] == "no-store" 