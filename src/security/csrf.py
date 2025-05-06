from pydantic_settings import BaseSettings
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi import Response, Request

class CsrfSettings(BaseSettings):
    secret_key: str = "INSECURE_SECRET_KEY_CHANGE_IN_PRODUCTION"
    # Add other settings if needed, like:
    # cookie_secure: bool = True # Set to True in production with HTTPS
    # header_name: str = "X-CSRF-Token"
    # cookie_samesite: str = "strict"

def handle_csrf_error(exc: CsrfProtectError):
    """Handles CsrfProtectError by returning a consistent error format."""
    return {
        "error_code": "INVALID_CSRF",
        "message": exc.message
    } 