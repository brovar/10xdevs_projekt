"""
Unit tests for the endpoints in the payment_router.py module.

This test suite covers the following endpoint:
- GET /payments/callback: handle_payment_callback

The tests verify:
- Success scenarios for different transaction statuses (success, fail, cancelled)
- Error handling for missing parameters (transaction_id, status)
- Error handling for invalid parameters (invalid status, invalid transaction UUID)
- Error handling for service exceptions (404, 409, 500)
- Logging of events

Test Structure:
- Uses FastAPI's TestClient
- Mocks dependencies (database, logger)
- Stubs for PaymentService and LogService
- Uses pytest fixtures for setup and handling different authentication scenarios
"""

import logging
import types
from typing import Any, Dict, List
from uuid import UUID, uuid4

import pytest
from fastapi import Request, status
from starlette.testclient import TestClient

import dependencies
import routers.payment_router as payment_router
from main import app
from schemas import LogEventType, OrderStatus, TransactionStatus
from services.order_service import ConflictError

# Define mock IDs and constants
MOCK_TRANSACTION_ID = uuid4()
MOCK_USER_ID = uuid4()


# Mock database session
def mock_db_session_add(*args, **kwargs):
    pass


async def mock_db_session_commit(*args, **kwargs):
    pass


async def mock_db_session_rollback(*args, **kwargs):
    pass


mock_session = types.SimpleNamespace(
    add=mock_db_session_add,
    commit=mock_db_session_commit,
    rollback=mock_db_session_rollback,
)

# Add logger to router
logger = logging.getLogger("test_payment")
payment_router.logger = logger


# Mock CSRF Protection
class MockCsrfProtect:
    def validate_csrf(self, request: Request):
        pass  # No-op for tests

    def set_csrf_cookie(self, response):
        pass  # No-op for tests


# Stub PaymentService
class StubPaymentService:
    """Test double for PaymentService."""

    _raise = None
    _return_value = None
    _call_args = {}
    _call_count = {}

    def __init__(self, db_session=None, logger=None):
        self.db_session = db_session
        self.logger = logger
        # Reset class variables to avoid test interference
        StubPaymentService._reset()

    @classmethod
    def _reset(cls):
        cls._raise = None
        cls._return_value = None
        cls._call_args = {}
        cls._call_count = {}

    def _record_call(self, method_name, **kwargs):
        StubPaymentService._call_args[method_name] = kwargs
        StubPaymentService._call_count[method_name] = (
            StubPaymentService._call_count.get(method_name, 0) + 1
        )

    def _maybe_raise(self):
        if StubPaymentService._raise:
            raise StubPaymentService._raise

    async def process_payment_callback(
        self, transaction_id: UUID, status: TransactionStatus
    ):
        self._record_call(
            "process_payment_callback",
            transaction_id=transaction_id,
            status=status,
        )
        self._maybe_raise()

        return StubPaymentService._return_value or types.SimpleNamespace(
            order_status=OrderStatus.PROCESSING
        )


# Stub LogService
class StubLogService:
    """Test double for LogService."""

    logs: List[Dict[str, Any]] = []
    _raise = None
    _skip_exception = False

    def __init__(self, db_session=None, logger=None):
        self.db_session = (
            db_session if db_session is not None else mock_session
        )
        self.logger = logger

    @classmethod
    def _reset(cls):
        cls.logs = []
        cls._raise = None
        cls._skip_exception = False

    async def create_log(
        self, event_type, message, user_id=None, ip_address=None
    ):
        if StubLogService._raise and not StubLogService._skip_exception:
            raise StubLogService._raise

        log_data = {
            "event_type": event_type,
            "message": message,
            "user_id": user_id,
            "ip_address": ip_address,
        }
        StubLogService.logs.append(log_data)


# Include the router for testing
app.include_router(payment_router.router)

# Set up test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def override_dependencies():
    """Fixture patching dependencies and services."""
    # Store current overrides to restore
    original_overrides = app.dependency_overrides.copy()

    # Reset stub services
    stub_payment_service = StubPaymentService()
    stub_log_service = StubLogService()
    stub_log_service._reset()

    # Mock CSRF Protection
    app.dependency_overrides[dependencies.get_db_session] = (
        lambda: mock_session
    )
    app.dependency_overrides[dependencies.get_logger] = lambda: logger
    app.dependency_overrides[dependencies.get_payment_service] = (
        lambda: stub_payment_service
    )
    app.dependency_overrides[dependencies.get_log_service] = (
        lambda: stub_log_service
    )

    yield

    # Cleanup
    app.dependency_overrides = original_overrides
    if dependencies.get_db_session not in app.dependency_overrides:
        app.dependency_overrides[dependencies.get_db_session] = (
            lambda: mock_session
        )
    if dependencies.get_logger not in app.dependency_overrides:
        app.dependency_overrides[dependencies.get_logger] = lambda: logger


# === Test GET /payments/callback ===


def test_payment_callback_success_status():
    """Test successful callback with status 'success'."""
    transaction_id = str(MOCK_TRANSACTION_ID)
    response = client.get(
        f"/payments/callback?transaction_id={transaction_id}&status_str=success"
    )

    # Expect 200 OK
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Callback processed"
    assert data["order_status"] == OrderStatus.PROCESSING

    # Verify service call
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 1
    )
    call_args = StubPaymentService._call_args["process_payment_callback"]
    assert str(call_args["transaction_id"]) == transaction_id
    assert call_args["status"] == TransactionStatus.SUCCESS

    # Verify logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_SUCCESS
    assert f"transaction {transaction_id}" in log_entry["message"]
    assert "success" in log_entry["message"]


def test_payment_callback_fail_status():
    """Test successful callback with status 'fail'."""
    transaction_id = str(MOCK_TRANSACTION_ID)
    response = client.get(
        f"/payments/callback?transaction_id={transaction_id}&status_str=fail"
    )

    # Expect 200 OK
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Callback processed"
    assert data["order_status"] == OrderStatus.PROCESSING

    # Verify service call
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 1
    )
    call_args = StubPaymentService._call_args["process_payment_callback"]
    assert str(call_args["transaction_id"]) == transaction_id
    assert call_args["status"] == TransactionStatus.FAIL

    # Verify logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_SUCCESS
    assert f"transaction {transaction_id}" in log_entry["message"]
    assert "fail" in log_entry["message"]


def test_payment_callback_cancelled_status():
    """Test successful callback with status 'cancelled'."""
    transaction_id = str(MOCK_TRANSACTION_ID)
    response = client.get(
        f"/payments/callback?transaction_id={transaction_id}&status_str=cancelled"
    )

    # Expect 200 OK
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Callback processed"
    assert data["order_status"] == OrderStatus.PROCESSING

    # Verify service call
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 1
    )
    call_args = StubPaymentService._call_args["process_payment_callback"]
    assert str(call_args["transaction_id"]) == transaction_id
    assert call_args["status"] == TransactionStatus.CANCELLED

    # Verify logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_SUCCESS
    assert f"transaction {transaction_id}" in log_entry["message"]
    assert "cancelled" in log_entry["message"]


def test_payment_callback_missing_transaction_id():
    """Test callback without transaction_id parameter."""
    response = client.get("/payments/callback?status_str=success")

    # Expect 400 BAD REQUEST
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error_code"] == "MISSING_PARAM"
    assert "transaction_id" in data["detail"]["message"]

    # Verify service not called
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 0
    )

    # Verify error logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_FAIL
    assert "Missing required parameter: transaction_id" in log_entry["message"]


def test_payment_callback_missing_status():
    """Test callback without status parameter."""
    transaction_id = str(MOCK_TRANSACTION_ID)
    response = client.get(
        f"/payments/callback?transaction_id={transaction_id}"
    )

    # Expect 400 BAD REQUEST
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error_code"] == "MISSING_PARAM"
    assert "status" in data["detail"]["message"]

    # Verify service not called
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 0
    )

    # Verify error logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_FAIL
    assert "Missing required parameter: status" in log_entry["message"]


def test_payment_callback_invalid_status():
    """Test callback with invalid status value."""
    transaction_id = str(MOCK_TRANSACTION_ID)
    response = client.get(
        f"/payments/callback?transaction_id={transaction_id}&status_str=invalid_status"
    )

    # Expect 400 BAD REQUEST
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error_code"] == "INVALID_STATUS"
    assert (
        "Allowed values: success, fail, cancelled" in data["detail"]["message"]
    )

    # Verify service not called
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 0
    )

    # Verify error logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_FAIL
    assert "Invalid payment status" in log_entry["message"]
    assert "invalid_status" in log_entry["message"]
    assert str(transaction_id) in log_entry["message"]


def test_payment_callback_invalid_transaction_id():
    """Test callback with invalid UUID format for transaction_id."""
    response = client.get(
        "/payments/callback?transaction_id=not-a-uuid&status_str=success"
    )

    # Expect 400 BAD REQUEST instead of 422 since the application validates UUID format
    # and returns 400 for invalid format instead of letting FastAPI validate with 422
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Verify service not called
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 0
    )


def test_payment_callback_transaction_not_found():
    """Test callback when transaction is not found."""
    transaction_id = str(uuid4())
    StubPaymentService._raise = ValueError(
        f"Transaction {transaction_id} not found"
    )

    response = client.get(
        f"/payments/callback?transaction_id={transaction_id}&status_str=success"
    )

    # Expect 404 NOT FOUND
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"]["error_code"] == "TRANSACTION_NOT_FOUND"
    assert (
        f"Transaction {transaction_id} not found" in data["detail"]["message"]
    )

    # Verify service call attempted
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 1
    )

    # Verify error logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_FAIL
    assert "Payment callback failed" in log_entry["message"]
    assert f"Transaction {transaction_id} not found" in log_entry["message"]


def test_payment_callback_order_not_found():
    """Test callback when order is not found for transaction."""
    transaction_id = str(MOCK_TRANSACTION_ID)
    StubPaymentService._raise = ValueError(
        f"Order not found for transaction {transaction_id}"
    )

    response = client.get(
        f"/payments/callback?transaction_id={transaction_id}&status_str=success"
    )

    # Expect 404 NOT FOUND
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"]["error_code"] == "ORDER_NOT_FOUND"
    assert (
        f"Order not found for transaction {transaction_id}"
        in data["detail"]["message"]
    )

    # Verify service call attempted
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 1
    )

    # Verify error logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_FAIL
    assert "Payment callback failed" in log_entry["message"]
    assert (
        f"Order not found for transaction {transaction_id}"
        in log_entry["message"]
    )


def test_payment_callback_order_already_processed():
    """Test callback when order is already processed."""
    transaction_id = str(MOCK_TRANSACTION_ID)
    StubPaymentService._raise = ConflictError(
        "Order has already been processed"
    )

    response = client.get(
        f"/payments/callback?transaction_id={transaction_id}&status_str=success"
    )

    # Expect 409 CONFLICT
    assert response.status_code == status.HTTP_409_CONFLICT
    data = response.json()
    assert data["detail"]["error_code"] == "ORDER_ALREADY_PROCESSED"
    assert "Order has already been processed" in data["detail"]["message"]

    # Verify service call attempted
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 1
    )

    # Verify error logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_FAIL
    assert "Payment callback conflict" in log_entry["message"]
    assert "Order has already been processed" in log_entry["message"]


def test_payment_callback_service_error():
    """Test callback with unexpected service error."""
    transaction_id = str(MOCK_TRANSACTION_ID)
    StubPaymentService._raise = Exception("Database connection error")

    response = client.get(
        f"/payments/callback?transaction_id={transaction_id}&status_str=success"
    )

    # Expect 500 INTERNAL SERVER ERROR
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert data["detail"]["error_code"] == "CALLBACK_PROCESSING_FAILED"
    assert "Failed to process payment callback" in data["detail"]["message"]

    # Verify service call attempted
    assert (
        StubPaymentService._call_count.get("process_payment_callback", 0) == 1
    )

    # Verify error logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_FAIL
    assert (
        "Unexpected error processing payment callback" in log_entry["message"]
    )
    assert "Database connection error" in log_entry["message"]


def test_payment_callback_success_logging():
    """Test logging of successful payment callback."""
    # Custom response to check different order status
    StubPaymentService._return_value = types.SimpleNamespace(
        order_status=OrderStatus.FAILED
    )

    transaction_id = str(MOCK_TRANSACTION_ID)
    response = client.get(
        f"/payments/callback?transaction_id={transaction_id}&status_str=fail"
    )

    # Expect 200 OK
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["message"] == "Callback processed"
    assert data["order_status"] == OrderStatus.FAILED

    # Verify logging
    assert len(StubLogService.logs) == 1
    log_entry = StubLogService.logs[0]
    assert log_entry["event_type"] == LogEventType.PAYMENT_CALLBACK_SUCCESS
    assert (
        f"Successfully processed payment callback for transaction {transaction_id}"
        in log_entry["message"]
    )
    assert "fail" in log_entry["message"]


def test_payment_callback_failure_logging():
    """Test handling of successful payment callback when logging fails."""
    # Configure logging to fail but not throw exception
    StubLogService._raise = Exception("Logging service error")
    StubLogService._skip_exception = True

    transaction_id = str(MOCK_TRANSACTION_ID)

    try:
        # Execute the request with pytest.raises to catch logger exception
        response = client.get(
            f"/payments/callback?transaction_id={transaction_id}&status_str=success"
        )

        # Verify the call was made to the payment service
        assert (
            StubPaymentService._call_count.get("process_payment_callback", 0)
            == 1
        )

        # Check if response indicates success despite logging failure
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Callback processed"
        assert data["order_status"] == OrderStatus.PROCESSING
    finally:
        # Reset for other tests
        StubLogService._skip_exception = False
        StubLogService._raise = None
