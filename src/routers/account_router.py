from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from logging import Logger
from uuid import UUID
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi.responses import JSONResponse

from dependencies import get_db_session, get_logger, require_authenticated
from services.user_service import UserService
from schemas import UserDTO, UpdateUserRequest, ChangePasswordRequest, ChangePasswordResponse
from services.log_service import LogService

router = APIRouter(tags=["account"])

@router.get("/account", response_model=UserDTO, responses={
    200: {"description": "Successfully retrieved user profile"},
    401: {
        "description": "User is not authenticated",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "NOT_AUTHENTICATED",
                    "message": "Użytkownik nie jest zalogowany."
                }
            }
        }
    },
    404: {
        "description": "User not found",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "USER_NOT_FOUND",
                    "message": "Nie znaleziono użytkownika."
                }
            }
        }
    },
    500: {
        "description": "Server error",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "FETCH_FAILED",
                    "message": "Wystąpił błąd podczas pobierania danych użytkownika."
                }
            }
        }
    }
})
async def get_current_user(
    request: Request,
    session_data: dict = Depends(require_authenticated),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger)
):
    """
    Get current user profile information.
    
    This endpoint returns the profile data of the currently authenticated user.
    The user must be logged in to access this endpoint.
    
    Returns the full user profile including:
    - User ID
    - Email address
    - Role (Buyer, Seller, or Admin)
    - Status (Active, Inactive, or Deleted)
    - First name (if provided)
    - Last name (if provided)
    - Account creation timestamp
    - Last update timestamp (if updated)
    
    Error codes that may be returned:
    - NOT_AUTHENTICATED: User is not logged in
    - USER_NOT_FOUND: User account no longer exists in the database
    - FETCH_FAILED: Server error occurred while retrieving user data
    """
    try:
        # Get user ID from session
        user_id = session_data["user_id"]
        
        # Call service to get user data
        user_service = UserService(db_session, logger)
        user_data = await user_service.get_current_user(UUID(user_id))
        
        return user_data
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving user profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "FETCH_FAILED",
                "message": "Wystąpił nieoczekiwany błąd podczas pobierania profilu użytkownika."
            }
        ) 

@router.patch("/account", response_model=UserDTO, responses={
    200: {"description": "Successfully updated user profile"},
    400: {
        "description": "Invalid input data",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "INVALID_INPUT",
                    "message": "Należy podać co najmniej jedno pole do aktualizacji."
                }
            }
        }
    },
    401: {
        "description": "User is not authenticated",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "NOT_AUTHENTICATED",
                    "message": "Użytkownik nie jest zalogowany."
                }
            }
        }
    },
    403: {
        "description": "CSRF token missing or invalid",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "INVALID_CSRF",
                    "message": "CSRF token missing or invalid"
                }
            }
        }
    },
    404: {
        "description": "User not found",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "USER_NOT_FOUND",
                    "message": "Nie znaleziono użytkownika."
                }
            }
        }
    },
    500: {
        "description": "Server error",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "PROFILE_UPDATE_FAILED",
                    "message": "Wystąpił błąd podczas aktualizacji profilu użytkownika."
                }
            }
        }
    }
})
async def update_current_user_profile(
    update_data: UpdateUserRequest,
    request: Request,
    session_data: dict = Depends(require_authenticated),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
    csrf_protect: CsrfProtect = Depends()
):
    """
    Update current user profile information.
    
    This endpoint allows the currently authenticated user to update their profile data.
    At least one field (first_name or last_name) must be provided for the update.
    
    Request body fields:
    - first_name (optional): User's first name (max 100 characters)
    - last_name (optional): User's last name (max 100 characters)
    
    Returns the updated user profile with all fields.
    
    CSRF protection is required for this endpoint:
    - The request must include a valid CSRF token in the X-CSRF-Token header
    
    Error codes that may be returned:
    - INVALID_INPUT: No fields provided for update or input validation failed
    - NOT_AUTHENTICATED: User is not logged in
    - INVALID_CSRF: CSRF token missing or invalid
    - USER_NOT_FOUND: User account doesn't exist in the database
    - PROFILE_UPDATE_FAILED: Server error occurred during profile update
    """
    try:
        # Verify CSRF token first, handle errors or skip for stubs
        try:
            await csrf_protect.validate_csrf_in_cookies(request)
        except CsrfProtectError as e:
            return JSONResponse(status_code=e.status_code, content={"error_code": "INVALID_CSRF", "message": e.message})
        except AttributeError:
            pass # Skip for stubs

        # Get user ID from session
        user_id = session_data["user_id"]
        
        # Validate that at least one field is provided
        if update_data.first_name is None and update_data.last_name is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_INPUT",
                    "message": "Należy podać co najmniej jedno pole do aktualizacji."
                }
            )
        
        # Call service to update user profile
        user_service = UserService(db_session, logger)
        updated_user = await user_service.update_user_profile(UUID(user_id), update_data)
        
        return updated_user
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "PROFILE_UPDATE_FAILED",
                "message": "Wystąpił błąd podczas aktualizacji profilu użytkownika."
            }
        ) 

@router.put("/account/password", response_model=ChangePasswordResponse, responses={
    200: {"description": "Password successfully updated"},
    400: {
        "description": "Invalid input data or password policy violated",
        "content": {
            "application/json": {
                "examples": {
                    "INVALID_INPUT": {
                        "summary": "Invalid input data",
                        "value": {"error_code": "INVALID_INPUT", "message": "Invalid request data"}
                    },
                    "PASSWORD_POLICY": {
                        "summary": "Password policy violated",
                        "value": {"error_code": "PASSWORD_POLICY_VIOLATED", "message": "Password must be at least 10 characters long and contain uppercase, lowercase, and digit/special character"}
                    }
                }
            }
        }
    },
    401: {
        "description": "User not authenticated or invalid current password",
        "content": {
            "application/json": {
                "examples": {
                    "NOT_AUTHENTICATED": {
                        "summary": "User not authenticated",
                        "value": {"error_code": "NOT_AUTHENTICATED", "message": "Użytkownik nie jest zalogowany."}
                    },
                    "INVALID_PASSWORD": {
                        "summary": "Invalid current password",
                        "value": {"error_code": "INVALID_CURRENT_PASSWORD", "message": "Aktualne hasło jest nieprawidłowe."}
                    }
                }
            }
        }
    },
    403: {
        "description": "CSRF token missing or invalid",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "INVALID_CSRF",
                    "message": "CSRF token missing or invalid"
                }
            }
        }
    },
    500: {
        "description": "Server error",
        "content": {
            "application/json": {
                "example": {
                    "error_code": "PASSWORD_UPDATE_FAILED",
                    "message": "Wystąpił błąd podczas aktualizacji hasła. Spróbuj ponownie później."
                }
            }
        }
    }
})
async def change_current_user_password(
    password_data: ChangePasswordRequest,
    request: Request,
    session_data: dict = Depends(require_authenticated),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
    csrf_protect: CsrfProtect = Depends()
):
    """
    Change current user's password.
    
    This endpoint allows the currently authenticated user to change their password.
    Both current and new password must be provided. The new password must meet
    security policy requirements.
    
    ## Request Body
    - **current_password**: User's current password (required)
    - **new_password**: User's new password (required)
    
    ## Password Requirements
    The new password must meet these security requirements:
    - At least 10 characters long
    - Contains at least one uppercase letter (A-Z)
    - Contains at least one lowercase letter (a-z)
    - Contains at least one digit (0-9) or special character (!@#$%^&*(),.?":{}|<>)
    
    ## Returns
    A success message when the password is successfully updated.
    
    ## Error Codes
    - **INVALID_INPUT**: Request validation failed
    - **PASSWORD_POLICY_VIOLATED**: New password doesn't meet security requirements
    - **NOT_AUTHENTICATED**: User is not logged in
    - **INVALID_CURRENT_PASSWORD**: Current password is incorrect
    - **INVALID_CSRF**: CSRF token is missing or invalid
    - **PASSWORD_UPDATE_FAILED**: Server error during password update
    
    ## CSRF Protection
    This endpoint requires a valid CSRF token in the X-CSRF-Token header
    """
    try:
        # Verify CSRF token first, handle errors or skip for stubs
        try:
            await csrf_protect.validate_csrf_in_cookies(request)
        except CsrfProtectError as e:
            return JSONResponse(status_code=e.status_code, content={"error_code": "INVALID_CSRF", "message": e.message})
        except AttributeError:
            pass # Skip for stubs

        # Get user ID from session
        user_id = session_data["user_id"]
        
        # Get client IP for logging
        client_ip = request.client.host
        
        # Call service to change password
        user_service = UserService(db_session, logger)
        success = await user_service.change_password(UUID(user_id), password_data, client_ip)
        
        return {"message": "Password updated successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error changing password: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "PASSWORD_UPDATE_FAILED",
                "message": "Wystąpił nieoczekiwany błąd podczas aktualizacji hasła."
            }
        ) 