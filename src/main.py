from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.exceptions import RequestValidationError
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi.responses import JSONResponse
import os
import sys
# Ensure src directory is in Python path for top-level imports
sys.path.insert(0, os.path.dirname(__file__))

from routers.auth_router import router as auth_router
from routers.seller_router import router as seller_router
from routers.buyer_router import router as buyer_router
from routers.account_router import router as account_router
from routers.category_router import router as category_router
from routers.offer_router import router as offer_router
from routers.order_router import router as order_router
from routers.media_router import router as media_router
from routers.admin_router import router as admin_router
from security.csrf import CsrfSettings, handle_csrf_error

# Create FastAPI app
app = FastAPI(
    title="SteamBay API",
    description="""
# SteamBay API Documentation

## Overview
SteamBay is an e-commerce platform for digital game sales. This API provides endpoints for user authentication, offer management, order processing, and more.

## Authentication Flow

### Registration
1. Use the `/auth/register` endpoint to create a new user account
2. Provide a valid email, password, and role (Buyer or Seller)
3. Password must meet security requirements (see endpoint documentation)
4. Upon successful registration, you'll receive the user details

### Login
1. Use the `/auth/login` endpoint with your email and password
2. On success, the API will set a secure HttpOnly cookie containing your session
3. The API will also set a CSRF token cookie and return it in the X-CSRF-Token header
4. Store the CSRF token in your client application for protected requests

### Protected Requests
1. Include the session cookie in all requests (browsers do this automatically)
2. For state-changing operations (POST, PUT, DELETE), include the CSRF token in the X-CSRF-Token header
3. The server will verify your authentication and authorization before processing the request

### Logout
1. Use the `/auth/logout` endpoint to terminate your session
2. Include the CSRF token in the X-CSRF-Token header
3. The server will clear your session cookie

## Role-Based Access Control
The API implements role-based access control with the following roles:

### Buyer Role
- Can browse and purchase products
- Can view own profile and order history
- Can't create or manage offers

### Seller Role
- Can create and manage offers
- Can view order statistics and sales data
- Has access to seller-specific endpoints under `/seller/*`
- Also has all Buyer permissions

### Admin Role
- Has all permissions of both Buyer and Seller
- Can access additional administrative features
- Can manage users and moderate content

## Authentication Errors

When authentication fails, you'll receive one of these error responses:

### 401 Unauthorized
```json
{
  "error_code": "NOT_AUTHENTICATED",
  "message": "Użytkownik nie jest zalogowany."
}
```
This means you need to log in before accessing this resource.

### 403 Forbidden
```json
{
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "message": "Nie masz uprawnień do wykonania tej operacji."
}
```
This means your account doesn't have the required role to access this resource.

## CSRF Protection

For security, all state-changing operations (POST, PUT, DELETE) require CSRF protection:

1. After logging in, you'll receive a CSRF token in both:
   - The `csrf_token` cookie 
   - The `X-CSRF-Token` response header
2. Store this token in your client application
3. Include it in the `X-CSRF-Token` header for all state-changing requests
4. If you don't include the token, you'll receive a 403 Forbidden response

## Error Handling
The API returns consistent error responses with the following structure:
```json
{
  "error_code": "ERROR_CODE",
  "message": "Human-readable error message"
}
```

Common error codes include:
- `INVALID_INPUT` - Request validation failed
- `INVALID_CREDENTIALS` - Authentication failed
- `NOT_AUTHENTICATED` - User is not logged in
- `INSUFFICIENT_PERMISSIONS` - User doesn't have permission to access this resource
- `EMAIL_ALREADY_EXISTS` - A user with this email already exists
- `INVALID_PASSWORD` - Password doesn't meet the security requirements
- `USER_INACTIVE` - User account is not active
- `INVALID_CSRF` - CSRF token is missing or invalid
- `RESOURCE_NOT_FOUND` - Requested resource doesn't exist
- `SERVER_ERROR` - Internal server error
    """,
    version="0.1.0",
    docs_url=None,  # Disable default docs
    redoc_url=None  # Disable default redoc
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure CSRF Protection
@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

# CSRF exception handler
@app.exception_handler(CsrfProtectError)
async def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(
        status_code=403,
        content=handle_csrf_error(exc)
    )

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "INVALID_INPUT",
            "message": "Invalid request data",
            "detail": str(exc)
        }
    )

# Include routers
app.include_router(auth_router)
app.include_router(seller_router)
app.include_router(buyer_router)
app.include_router(account_router)
app.include_router(category_router)
app.include_router(offer_router)
app.include_router(order_router)
app.include_router(media_router)
app.include_router(admin_router)

# Custom OpenAPI and docs endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        swagger_favicon_url="/favicon.ico"
    )

@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_schema():
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"] = {
        "securitySchemes": {
            "cookieAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "steambay_session"
            },
            "csrfToken": {
                "type": "apiKey",
                "in": "header",
                "name": "X-CSRF-Token"
            }
        }
    }
    
    # Add security to all endpoints except login and register
    for path in openapi_schema["paths"]:
        if not (path == "/auth/login" or path == "/auth/register"):
            for method in openapi_schema["paths"][path]:
                openapi_schema["paths"][path][method]["security"] = [
                    {"cookieAuth": []},
                    {"csrfToken": []}
                ]
    
    # Add API version info to title
    openapi_schema["info"]["title"] = f"{openapi_schema['info']['title']} v{app.version}"
    
    return openapi_schema

@app.get("/", summary="API welcome page", description="Returns a welcome message to confirm the API is running.")
async def root():
    """
    Root endpoint that confirms the API is running.
    
    Returns:
        dict: Welcome message
    """
    return {
        "message": "Welcome to SteamBay API",
        "version": app.version,
        "docs_url": "/docs"
    }

@app.get("/health", summary="API health status", description="Returns the health status of the API for monitoring purposes.")
async def health_check():
    """
    Health check endpoint for monitoring API status.
    
    Returns:
        dict: Health status
    """
    return {
        "status": "ok",
        "api_version": app.version
    } 