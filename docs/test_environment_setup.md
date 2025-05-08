# Test Environment Setup

## Overview

This document describes the test environment setup for the SteamBay application, particularly the shared services architecture between frontend and backend components.

## Shared Services Architecture

The SteamBay application uses a shared service architecture where business logic services are located in `frontend/src/services/` but are used by both the frontend and backend components. This design:

1. **Promotes code reuse**: Core business logic is defined once and used in both frontend and backend
2. **Ensures consistency**: The same validation rules and business logic apply throughout the application
3. **Simplifies maintenance**: Changes to business logic affect both frontend and backend consistently

### Directory Structure

```
/
├── frontend/
│   └── src/
│       └── services/   <-- SHARED SERVICES
└── src/                <-- BACKEND CODE
    └── routers/        <-- API ENDPOINTS
```

### Service Import Strategy

The test environment needs to make the services module available to both the frontend and backend code. This is accomplished through Python path manipulation in the `tests/conftest.py` file:

```python
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
# Add frontend/src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src')))
```

This allows imports like:

```python
from services.auth_service import AuthService
```

to work correctly during test execution.

## Running Tests

To run the tests:

```bash
# Run all tests
python -m pytest tests/

# Run tests for a specific router
python -m pytest tests/test_auth_router.py

# Run tests with verbose output
python -m pytest tests/ -v

# Run tests with coverage report
python -m pytest tests/ --cov=src --cov-report=term
```

## Test Organization

The tests are organized by router, with one test file per router:

- `test_account_router.py`
- `test_admin_router.py`
- `test_auth_router.py`
- `test_buyer_router.py`
- `test_category_router.py`
- `test_media_router.py`
- `test_offer_router.py`
- `test_order_router.py`
- `test_payment_router.py`
- `test_seller_router.py`

Each test file follows a similar structure:

1. Mock service implementations
2. Test client setup
3. Individual test functions for each endpoint and scenario

## Dependencies and Mocking

The tests use dependency injection to replace real services with mocks:

```python
app.dependency_overrides[dependencies.get_db_session] = lambda: None
app.dependency_overrides[dependencies.get_logger] = lambda: DummyLogger()
```

This allows tests to run without a database connection and with predictable service behavior.

## Common Issues and Solutions

### Circular Imports

When creating the shared services architecture, be careful with circular imports. Keep the `__init__.py` file in the services directory empty to avoid circular imports between services and dependencies.

### Path Resolution

If you encounter "ModuleNotFoundError" when running tests, check that:
1. The `conftest.py` file is properly adding the necessary directories to the Python path
2. You're running pytest from the project root directory

## Future Improvements

1. Consider using a more formal package structure for the shared services
2. Add more comprehensive documentation in each service module
3. Consider moving to a monorepo structure with better package management 