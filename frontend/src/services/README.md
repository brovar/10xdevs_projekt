# Services Module

This directory contains all service classes used by both the frontend and backend components of the SteamBay application.

## Architecture Note

These service classes are shared between the frontend and backend through Python path manipulation. The directory structure is:

```
/
├── frontend/
│   └── src/
│       └── services/   <-- THIS DIRECTORY
└── src/
    └── (backend code)
```

When running tests, the `tests/conftest.py` file adds both `src/` and `frontend/src/` to the Python path, allowing imports like:

```python
from services.auth_service import AuthService
```

## Available Services

- **AuthService**: Handles user authentication, registration, and session management
- **SessionService**: Manages user sessions and cookies
- **UserService**: User profile and account management
- **OrderService**: Order processing and management
- **LogService**: Logging of system events and errors
- **PaymentService**: Payment processing
- **OfferService**: Product offerings and catalog management
- **MediaService**: Handling of image and media uploads/downloads
- **CategoryService**: Product categorization
- **FileService**: File uploading and downloading
- **ValidationService**: Input validation helpers

## Best Practices

1. Keep business logic in these service classes, not in routers
2. Use dependency injection for testability
3. Follow FastAPI's async patterns for DB operations
4. Keep services focused on single responsibilities
5. Use proper error handling with custom exceptions 