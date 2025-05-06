import pytest
from fastapi import FastAPI # Import FastAPI do stworzenia nowej instancji aplikacji
from fastapi.testclient import TestClient
from fastapi import status, HTTPException, Depends, Path, Request
from typing import Dict, Any, Optional, List
from uuid import uuid4, UUID
import logging
from datetime import datetime, timezone
from decimal import Decimal
from fastapi_csrf_protect import CsrfProtect
import types
import json # Import json for explicit serialization if needed

import dependencies
from routers.offer_router import router as offer_router # Importuj sam router
# from main import app # Już nie importujemy globalnej aplikacji
from schemas import (
    UserRole, LogEventType, OfferStatus, OfferDetailDTO,
    ErrorResponse, SellerInfoDTO, CategoryDTO
)
# Import service getter dependencies
from dependencies import get_offer_service, get_media_service, get_logger, require_seller, get_log_service

# Stwórz nową, czystą instancję FastAPI na potrzeby testów i dołącz router
test_app = FastAPI()
test_app.include_router(offer_router)

# Mock user IDs and other constants
MOCK_SELLER_ID = uuid4()
MOCK_BUYER_ID = uuid4()
MOCK_ADMIN_ID = uuid4()
MOCK_OFFER_ID = uuid4()

# --- Mock Dependencies and Services ---

# Define MockCsrfProtect class outside the fixture for clarity
class MockCsrfProtect:
    async def validate_csrf_in_cookies(self, request: Request):
        # Bypass CSRF validation for tests
        pass

# Stub LogService
class StubLogService:
    """Test double for LogService."""
    logs: List[Dict[str, Any]] = [] # Class variable to store logs across instances

    @classmethod
    def _reset(cls):
        cls.logs = []

    async def create_log(self, user_id, event_type, message, ip_address=None):
        # Ensure user_id is stored as string if it's a UUID object
        user_id_str = str(user_id) if isinstance(user_id, UUID) else user_id
        self.logs.append({
            "user_id": user_id_str,
            "event_type": event_type.value if hasattr(event_type, 'value') else event_type,
            "message": message,
            "ip_address": ip_address,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

# Stub OfferService
class StubOfferService:
    """Test double for OfferService."""
    _raise = None
    _return_value = None
    _call_args = {}
    _call_count = {}

    def __init__(self, db_session=None, logger=None, log_service: Optional[StubLogService] = None):
        self.log_service = log_service if log_service else StubLogService()

    @classmethod
    def _reset(cls):
        cls._raise = None
        cls._return_value = None
        cls._call_args = {}
        cls._call_count = {}
        StubLogService._reset()

    def _record_call(self, method_name, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, UUID):
                kwargs[key] = str(value)
        StubOfferService._call_args[method_name] = kwargs
        StubOfferService._call_count[method_name] = StubOfferService._call_count.get(method_name, 0) + 1

    def _maybe_raise(self):
        if StubOfferService._raise:
            raise StubOfferService._raise

    async def mark_offer_as_sold(self, offer_id: UUID, user_id: UUID, user_role: UserRole) -> OfferDetailDTO:
        self._record_call('mark_offer_as_sold', offer_id=offer_id, user_id=user_id, user_role=user_role)
        
        # Używamy poprawnego LogEventType.OFFER_STATUS_CHANGE
        await self.log_service.create_log(
            user_id=user_id,
            event_type=LogEventType.OFFER_STATUS_CHANGE, 
            message=f"Offer {offer_id} status changed to sold (simulated)" # Zaktualizowano wiadomość dla jasności
        )
        self._maybe_raise()

        # Zmodyfikowano mock_response_dict, aby zawierał zagnieżdżone seller i category
        mock_response_dict = {
            "id": str(offer_id),
            "category_id": 1, # To jest w OfferSummaryDTO, ale nie w OfferDetailDTO bezpośrednio (jest w category)
            "title": "Sold Offer",
            "price": 10.0, 
            "image_filename": "sold_offer.jpg",
            "quantity": 0,
            "status": OfferStatus.SOLD.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "seller_id": str(user_id), # To też jest w OfferSummaryDTO
            # Pola specyficzne dla OfferDetailDTO (oprócz tych z OfferSummaryDTO)
            "description": "Mocked offer description",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "seller": { # Zagnieżdżony obiekt SellerInfoDTO
                "id": str(user_id),
                "first_name": "MockSellerFirst",
                "last_name": "MockSellerLast"
            },
            "category": { # Zagnieżdżony obiekt CategoryDTO
                "id": 1,
                "name": "MockCategory"
            }
            # Usunięto pola, które nie są wprost w OfferDetailDTO lub OfferSummaryDTO:
            # "is_active", "view_count", "condition", "main_image_url", "image_urls", "seller_username"
        }
        # Zwracamy ten słownik, FastAPI zwaliduje go względem OfferDetailDTO
        return StubOfferService._return_value or mock_response_dict

# Use a simple mock db session as done in test_order_router
def mock_db_session_add(*args, **kwargs):
    pass

async def mock_db_session_commit(*args, **kwargs):
    pass

async def mock_db_session_get(*args, **kwargs):
     return types.SimpleNamespace() # Return a dummy object if get is called

async def mock_db_session_rollback(*args, **kwargs):
    pass

async def mock_db_session_flush(*args, **kwargs):
    pass

mock_session = types.SimpleNamespace(
    add=mock_db_session_add,
    commit=mock_db_session_commit,
    get=mock_db_session_get,
    rollback=mock_db_session_rollback,
    flush=mock_db_session_flush
)

# Helper to store and retrieve mock user data
current_user_data: Optional[Dict] = None

async def mock_require_seller():
    # This mock dependency replaces require_seller
    if current_user_data and current_user_data.get("role") == UserRole.SELLER:
        # Simulate returning a simple user object with id and role
        mock_user = types.SimpleNamespace(
            id=current_user_data.get("user_id"),
            role=current_user_data.get("role")
        )
        return mock_user
    else:
        # If not a seller or not authenticated, raise HTTPException 403
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Only sellers can perform this operation."}
        )

# Fixtures to set mock user data
@pytest.fixture
def seller_auth():
    global current_user_data
    current_user_data = {
        'user_id': MOCK_SELLER_ID,
        'email': "seller@example.com",
        'role': UserRole.SELLER
    }
    yield
    current_user_data = None # Reset after test

@pytest.fixture
def buyer_auth():
    global current_user_data
    current_user_data = {
        'user_id': MOCK_BUYER_ID,
        'email': "buyer@example.com",
        'role': UserRole.BUYER
    }
    yield
    current_user_data = None # Reset after test

@pytest.fixture
def no_auth():
    global current_user_data
    current_user_data = None # No authenticated user
    yield
    current_user_data = None # Reset after test

# Fixture to override dependencies for tests
@pytest.fixture(autouse=True)
def override_dependencies_for_test_app(): # Zmieniono nazwę, aby odzwierciedlić użycie test_app
    original_overrides = test_app.dependency_overrides.copy()
    test_app.dependency_overrides[dependencies.get_db_session] = lambda: mock_session
    test_app.dependency_overrides[dependencies.get_logger] = lambda: logging.getLogger('test_offer_router')
    test_app.dependency_overrides[dependencies.get_offer_service] = get_offer_service_override
    # Override media service even if not used by this endpoint for consistency
    test_app.dependency_overrides[dependencies.get_media_service] = lambda: types.SimpleNamespace()
    test_app.dependency_overrides[dependencies.require_seller] = mock_require_seller
    test_app.dependency_overrides[CsrfProtect] = lambda: MockCsrfProtect()
    test_app.dependency_overrides[dependencies.get_log_service] = lambda: StubLogService()

    # Reset stubs before each test
    StubOfferService._reset()
    StubLogService._reset()

    yield # Run the test

    # Restore original dependencies after test
    test_app.dependency_overrides = original_overrides

# Create a TestClient instance
client = TestClient(test_app)

# --- Test Cases for /offers/{offer_id}/mark-sold ---

def test_mark_offer_as_sold_success(seller_auth):
    StubOfferService._return_value = None 
    response = client.post(f"/{MOCK_OFFER_ID}/mark-sold")

    if response.status_code != status.HTTP_200_OK:
        print("Response for failed success test:", response.json())

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(MOCK_OFFER_ID)
    assert response_data["status"] == OfferStatus.SOLD.value
    assert "seller" in response_data
    assert response_data["seller"]["id"] == str(MOCK_SELLER_ID)
    assert "category" in response_data
    assert response_data["category"]["id"] == 1

    assert StubOfferService._call_count.get('mark_offer_as_sold') == 1
    call_args = StubOfferService._call_args.get('mark_offer_as_sold')
    assert call_args['offer_id'] == str(MOCK_OFFER_ID)
    assert call_args['user_id'] == str(MOCK_SELLER_ID)
    assert call_args['user_role'] == UserRole.SELLER
    
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry['user_id'] == str(MOCK_SELLER_ID)
    assert log_entry['event_type'] == LogEventType.OFFER_STATUS_CHANGE.value
    assert f"Offer {MOCK_OFFER_ID} status changed to sold" in log_entry['message']

@pytest.mark.parametrize("error_status, error_code, error_message, service_exception_detail_dict", [
    (status.HTTP_404_NOT_FOUND, "OFFER_NOT_FOUND", "Offer not found", {"error_code": "OFFER_NOT_FOUND", "message": "Offer not found"}),
    (status.HTTP_409_CONFLICT, "INVALID_STATUS_TRANSITION", "Cannot mark offer with status 'archived' as sold", {"error_code": "INVALID_STATUS_TRANSITION", "message": "Cannot mark offer with status 'archived' as sold"}),
    (status.HTTP_409_CONFLICT, "ALREADY_SOLD", "Offer is already marked as sold", {"error_code": "ALREADY_SOLD", "message": "Offer is already marked as sold"}),
    (status.HTTP_403_FORBIDDEN, "NOT_OFFER_OWNER", "You can only mark your own offers as sold", {"error_code": "NOT_OFFER_OWNER", "message": "You can only mark your own offers as sold"}),
])
def test_mark_offer_as_sold_service_errors(seller_auth, error_status, error_code, error_message, service_exception_detail_dict):
    StubOfferService._raise = HTTPException(status_code=error_status, detail=service_exception_detail_dict)
    response = client.post(f"/{MOCK_OFFER_ID}/mark-sold")

    assert response.status_code == error_status
    response_json = response.json()
    
    # Oczekujemy struktury {'detail': {'error_code': ..., 'message': ...}}
    assert "detail" in response_json
    assert isinstance(response_json["detail"], dict)
    assert response_json["detail"].get("error_code") == error_code
    assert error_message in response_json["detail"].get("message", "")
    
    assert StubOfferService._call_count.get('mark_offer_as_sold') == 1
    assert len(StubLogService.logs) == 1 
    log_entry = StubLogService.logs[0]
    assert log_entry['user_id'] == str(MOCK_SELLER_ID)
    assert log_entry['event_type'] == LogEventType.OFFER_STATUS_CHANGE.value

def test_mark_offer_as_sold_server_error(seller_auth):
    StubOfferService._raise = Exception("Database connection failed")
    response = client.post(f"/{MOCK_OFFER_ID}/mark-sold")
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    response_json = response.json()
    # Oczekujemy struktury {'detail': {'error_code': ..., 'message': ...}}
    assert "detail" in response_json
    assert isinstance(response_json["detail"], dict)
    assert response_json["detail"].get("error_code") == "MARK_SOLD_FAILED"
    assert "An unexpected error occurred" in response_json["detail"].get("message", "")

    assert StubOfferService._call_count.get('mark_offer_as_sold') == 1
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry['user_id'] == str(MOCK_SELLER_ID)
    assert log_entry['event_type'] == LogEventType.OFFER_STATUS_CHANGE.value

def test_mark_offer_as_sold_not_authenticated(no_auth):
    response = client.post(f"/{MOCK_OFFER_ID}/mark-sold")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    response_json = response.json()
    # Oczekujemy struktury {'detail': {'error_code': ..., 'message': ...}}
    assert "detail" in response_json
    assert isinstance(response_json["detail"], dict)
    assert response_json["detail"].get("error_code") == "INSUFFICIENT_PERMISSIONS"
    assert "Only sellers can perform this operation." in response_json["detail"].get("message", "")

    assert StubOfferService._call_count.get('mark_offer_as_sold') is None
    assert len(StubLogService.logs) == 0

def test_mark_offer_as_sold_forbidden_role(buyer_auth):
    response = client.post(f"/{MOCK_OFFER_ID}/mark-sold")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    response_json = response.json()
    # Oczekujemy struktury {'detail': {'error_code': ..., 'message': ...}}
    assert "detail" in response_json
    assert isinstance(response_json["detail"], dict)
    assert response_json["detail"].get("error_code") == "INSUFFICIENT_PERMISSIONS"
    assert "Only sellers can perform this operation." in response_json["detail"].get("message", "")

    assert StubOfferService._call_count.get('mark_offer_as_sold') is None
    assert len(StubLogService.logs) == 0

def test_mark_offer_as_sold_invalid_uuid(seller_auth):
    invalid_uuid = "not-a-uuid"
    response = client.post(f"/{invalid_uuid}/mark-sold")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    response_data = response.json()
    assert "detail" in response_data
    assert isinstance(response_data["detail"], list)
    assert len(response_data["detail"]) > 0
    assert any("uuid" in err.get("type", "").lower() for err in response_data["detail"])
    assert StubOfferService._call_count.get('mark_offer_as_sold') is None
    assert len(StubLogService.logs) == 0

def get_offer_service_override():
    mock_log_service_instance = StubLogService() # Tworzymy instancję mocka LogService
    return StubOfferService(log_service=mock_log_service_instance) 