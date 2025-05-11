from pydantic_settings import BaseSettings
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi import Response, Request
import os

class CsrfSettings(BaseSettings):
    secret_key: str = os.environ.get("CSRF_SECRET_KEY", "INSECURE_SECRET_KEY_CHANGE_IN_PRODUCTION")
    cookie_secure: bool = False  # Set to True in production with HTTPS
    cookie_samesite: str = "lax"  # Use 'strict' in production
    header_name: str = "X-CSRF-Token"
    cookie_name: str = "fastapi-csrf-token"

def handle_csrf_error(exc: CsrfProtectError):
    """Handles CsrfProtectError by returning a consistent error format."""
    return {
        "error_code": "INVALID_CSRF",
        "message": exc.message
    } 