# Admin Router Test Guide

## Overview

This document explains the test coverage for the endpoints in `admin_router.py` which handles all administrative operations. The tests are located in `tests/test_admin_router.py`.

## Endpoints Covered

The test suite covers the following endpoints:

1. **GET /admin/users** - List all users with filtering options
2. **GET /admin/users/{user_id}** - Get details for a specific user
3. **POST /admin/users/{user_id}/block** - Block a user (set status to Inactive)
4. **POST /admin/users/{user_id}/unblock** - Unblock a user (set status to Active)
5. **GET /admin/offers** - List all offers with filtering options
6. **POST /admin/offers/{offer_id}/moderate** - Moderate an offer
7. **POST /admin/offers/{offer_id}/unmoderate** - Unmoderate an offer
8. **GET /admin/orders** - List all orders with filtering options
9. **POST /admin/orders/{order_id}/cancel** - Cancel an order
10. **GET /admin/logs** - List system logs with filtering options

## Test Coverage Metrics

The test suite achieves the following coverage:

- **Overall Coverage**: ~85% of code in `admin_router.py`
- **Number of Tests**: 64 test functions
- **Endpoint Coverage**: 100% (all endpoints are tested)
- **Authentication Scenarios**: 100% (all authentication states are tested)

To view the latest coverage report, run:
```bash
python -m pytest --cov=src.routers.admin_router tests/test_admin_router.py
```

## Test Coverage Areas

The test suite verifies:

### Authentication & Authorization
- Handling requests from authenticated admin users
- Handling requests from unauthenticated users
- Role-based access control (only admins can access)
- Access denied for non-admin roles (buyer, seller)

### Success Scenarios
- Proper HTTP status codes (200 OK for successful operations)
- Response body format and structure
- Default pagination parameters
- Resource updates (e.g., user status changes, order cancellation)

### Error Handling
- Mapping service exceptions to HTTP errors (400, 401, 403, 404, 409, 500)
- Invalid input validation (pagination parameters, filters)
- CSRF validation (for modifying operations)
- Proper error response format

### Filtering and Pagination
- Query parameter handling
- Filtering by various attributes
- Page and limit parameters
- Validation of pagination values

### Edge Cases
- Empty data results
- Resource not found
- Resources in conflicting states (e.g., already moderated offers)
- Invalid UUID formats
- Invalid date formats

## Mocking Strategy

The test suite uses several mocking approaches:

1. **Dependency Injection Overrides**: 
   - Mocks the dependencies used by the router (database session, logger)
   - Overrides authentication/role checks with custom fixtures

2. **Stub Service Classes**:
   - `StubUserService`: Simulates user management operations
   - `StubLogService`: Simulates logging operations
   - `StubOfferService`: Simulates offer management operations
   - `StubOrderService`: Simulates order management operations
   - Support controlled failures and custom returns

3. **Mock Database Session**:
   - Implements async mock functions for session operations
   - Uses `SimpleNamespace` for simple attribute-based access
   - `MockResult` class mimics SQLAlchemy result objects

4. **Authentication Mocking**:
   - Provides fixtures for different authentication states (admin, buyer, seller, none)
   - Simulates appropriate authentication contexts for testing different roles

## Test Organization

Tests are organized by endpoint with naming conventions that clearly indicate what is being tested:

1. **Auth-based tests**: Each endpoint has tests for unauthorized and forbidden access
   - `test_*_unauthorized`: Tests unauthenticated access  
   - `test_*_forbidden_role`: Tests access with insufficient permissions

2. **Success tests**:
   - `test_*_success`: Tests the happy path scenario
   - `test_*_with_filters`: Tests using query parameters/filters

3. **Error tests**:
   - `test_*_not_found`: Tests resource not found scenarios
   - `test_*_invalid_*`: Tests handling of invalid input
   - `test_*_service_error`: Tests handling of service-level errors

4. **CSRF tests**:
   - `test_*_csrf_invalid`: Tests CSRF validation for POST endpoints

## Notable Testing Patterns

1. **Fixture-based authentication**:
   ```python
   def test_some_endpoint(buyer_auth):  # Uses buyer authentication (should be forbidden)
       # Test code here
   ```

2. **Stub services with controllable behavior**:
   ```python
   # Configure stub to simulate a failure
   StubUserService._raise = ValueError("User not found")
   
   # Test endpoint
   response = client.get(f"/admin/users/{user_id}")
   
   # Verify expected error response
   assert response.status_code == status.HTTP_404_NOT_FOUND
   assert response.json()['detail']['error_code'] == "USER_NOT_FOUND"
   ```

3. **Call tracking in stub services**:
   ```python
   # After calling an endpoint, verify the service was called with expected args
   assert StubOfferService._call_count.get('moderate_offer', 0) == 1
   call_args = StubOfferService._call_args['moderate_offer']
   assert str(call_args['offer_id']) == offer_id
   ```

4. **Log verification**:
   ```python
   # Verify log was created with expected attributes
   assert len(StubLogService.logs) == 1
   log_entry = StubLogService.logs[0]
   assert log_entry['event_type'] == LogEventType.ADMIN_LIST_OFFERS
   assert "accessed offer list" in log_entry['message']
   ```

## Maintenance Notes

When adding new endpoints to the admin router, ensure:

1. Add corresponding test cases for:
   - Success scenarios
   - Authentication/authorization
   - Error handling
   - Edge cases

2. Follow the established naming conventions for tests

3. Update this guide to document new endpoint tests

4. Verify that all parameters and functionalities are covered 