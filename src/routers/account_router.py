from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db_session, get_logger, require_authenticated
from schemas import (ChangePasswordRequest, ChangePasswordResponse,
                     UpdateUserRequest, UserDTO)
from services.user_service import UserService

router = APIRouter(tags=["account"])


@router.get(
    "/account",
    response_model=UserDTO,
    responses={
        200: {"description": "Successfully retrieved user profile"},
        401: {
            "description": "User is not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "NOT_AUTHENTICATED",
                        "message": "User is not logged in.",
                    }
                }
            },
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "USER_NOT_FOUND",
                        "message": "User not found.",
                    }
                }
            },
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "FETCH_FAILED",
                        "message": "An error occurred while retrieving user data.",
                    }
                }
            },
        },
    },
)
async def get_current_user(
    request: Request,
    session_data: dict = Depends(require_authenticated),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
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
        logger.info(
            f"Getting profile for user ID: {user_id} (type: {type(user_id)})"
        )

        # Call service to get user data - convert to UUID only if it's a string
        user_service = UserService(db_session, logger)
        if isinstance(user_id, str):
            try:
                user_data = await user_service.get_current_user(UUID(user_id))
            except ValueError as e:
                logger.error(f"Invalid UUID format in session: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "INVALID_SESSION_DATA",
                        "message": "Session contains invalid data. Please log out and log in again.",
                    },
                )
        else:
            # Already a UUID object
            user_data = await user_service.get_current_user(user_id)

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
                "message": "An unexpected error occurred while retrieving user profile.",
            },
        )


@router.patch(
    "/account",
    response_model=UserDTO,
    responses={
        200: {"description": "Successfully updated user profile"},
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "INVALID_INPUT",
                        "message": "At least one field must be provided for update.",
                    }
                }
            },
        },
        401: {
            "description": "User is not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "NOT_AUTHENTICATED",
                        "message": "User is not logged in.",
                    }
                }
            },
        },
        403: {
            "description": "CSRF token missing or invalid",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "INVALID_CSRF",
                        "message": "CSRF token missing or invalid",
                    }
                }
            },
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "USER_NOT_FOUND",
                        "message": "User not found.",
                    }
                }
            },
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "PROFILE_UPDATE_FAILED",
                        "message": "An error occurred while updating user profile.",
                    }
                }
            },
        },
    },
)
async def update_current_user_profile(
    update_data: UpdateUserRequest,
    request: Request,
    session_data: dict = Depends(require_authenticated),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
    csrf_protect: CsrfProtect = Depends(),
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
        # Verify CSRF token
        try:
            csrf_protect.validate_csrf(request)
        except Exception as csrf_error:
            logger.error(f"CSRF validation failed: {str(csrf_error)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "INVALID_CSRF",
                    "message": "CSRF token missing or invalid",
                },
            )

        # Get user ID from session
        user_id = session_data["user_id"]
        logger.info(
            f"Updating profile for user ID: {user_id} (type: {type(user_id)})"
        )

        # Validate that at least one field is provided
        if update_data.first_name is None and update_data.last_name is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": "INVALID_INPUT",
                    "message": "At least one field must be provided for update.",
                },
            )

        # Call service to update user profile - convert to UUID only if it's a string
        user_service = UserService(db_session, logger)
        if isinstance(user_id, str):
            try:
                updated_user = await user_service.update_user_profile(
                    UUID(user_id), update_data
                )
            except ValueError as e:
                logger.error(f"Invalid UUID format in session: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "INVALID_SESSION_DATA",
                        "message": "Session contains invalid data. Please log out and log in again.",
                    },
                )
        else:
            # Already a UUID object
            updated_user = await user_service.update_user_profile(
                user_id, update_data
            )

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
                "message": "An error occurred while updating user profile.",
            },
        )


@router.put(
    "/account/password",
    response_model=ChangePasswordResponse,
    responses={
        200: {"description": "Password successfully updated"},
        400: {
            "description": "Invalid input data or password policy violated",
            "content": {
                "application/json": {
                    "examples": {
                        "INVALID_INPUT": {
                            "summary": "Invalid input data",
                            "value": {
                                "error_code": "INVALID_INPUT",
                                "message": "Invalid request data",
                            },
                        },
                        "PASSWORD_POLICY": {
                            "summary": "Password policy violated",
                            "value": {
                                "error_code": "PASSWORD_POLICY_VIOLATED",
                                "message": "Password must be at least 10 characters long and contain uppercase, lowercase, and digit/special character",
                            },
                        },
                    }
                }
            },
        },
        401: {
            "description": "User not authenticated or invalid current password",
            "content": {
                "application/json": {
                    "examples": {
                        "NOT_AUTHENTICATED": {
                            "summary": "User not authenticated",
                            "value": {
                                "error_code": "NOT_AUTHENTICATED",
                                "message": "User is not logged in.",
                            },
                        },
                        "INVALID_PASSWORD": {
                            "summary": "Invalid current password",
                            "value": {
                                "error_code": "INVALID_CURRENT_PASSWORD",
                                "message": "Current password is incorrect.",
                            },
                        },
                    }
                }
            },
        },
        403: {
            "description": "CSRF token missing or invalid",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "INVALID_CSRF",
                        "message": "CSRF token missing or invalid",
                    }
                }
            },
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "PASSWORD_CHANGE_FAILED",
                        "message": "An error occurred while changing the password. Please try again later.",
                    }
                }
            },
        },
    },
)
async def change_current_user_password(
    password_data: ChangePasswordRequest,
    request: Request,
    session_data: dict = Depends(require_authenticated),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
    csrf_protect: CsrfProtect = Depends(),
):
    """
    Change current user's password.

    This endpoint allows authenticated users to change their password.
    The user must provide their current password for verification
    and a new password that meets the password policy requirements.

    Password policy:
    - At least 10 characters
    - Must contain at least one uppercase letter
    - Must contain at least one lowercase letter
    - Must contain at least one digit or special character

    Request body:
    - current_password: User's current password for verification
    - new_password: The new password that complies with the password policy

    CSRF protection is required for this endpoint:
    - The request must include a valid CSRF token in the X-CSRF-Token header

    Error codes that may be returned:
    - INVALID_INPUT: Request data is invalid or missing required fields
    - PASSWORD_POLICY_VIOLATED: New password doesn't meet policy requirements
    - NOT_AUTHENTICATED: User is not logged in
    - INVALID_CURRENT_PASSWORD: Current password verification failed
    - INVALID_CSRF: CSRF token missing or invalid
    - USER_NOT_FOUND: User account doesn't exist in the database
    - PASSWORD_CHANGE_FAILED: Server error occurred during password change
    """
    try:
        # Verify CSRF token
        try:
            csrf_protect.validate_csrf(request)
        except Exception as csrf_error:
            logger.error(f"CSRF validation failed: {str(csrf_error)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "INVALID_CSRF",
                    "message": "CSRF token missing or invalid",
                },
            )

        # Get user ID from session
        user_id = session_data["user_id"]
        logger.info(
            f"Changing password for user ID: {user_id} (type: {type(user_id)})"
        )

        # Get client IP for logging
        client_ip = request.client.host

        # Call service to change password - convert to UUID only if it's a string
        user_service = UserService(db_session, logger)
        if isinstance(user_id, str):
            try:
                success = await user_service.change_password(
                    UUID(user_id), password_data, client_ip
                )
            except ValueError as e:
                logger.error(f"Invalid UUID format in session: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error_code": "INVALID_SESSION_DATA",
                        "message": "Session contains invalid data. Please log out and log in again.",
                    },
                )
        else:
            # Already a UUID object
            success = await user_service.change_password(
                user_id, password_data, client_ip
            )

        if success:
            return {"message": "Password has been changed successfully."}
        else:
            # This should not happen normally, because change_password should raise an exception on failure
            logger.warning(
                f"Password change for user {user_id} returned false without raising an exception"
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "error_code": "PASSWORD_CHANGE_FAILED",
                    "message": "An error occurred while changing the password. Please try again later.",
                },
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error changing password: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "PASSWORD_CHANGE_FAILED",
                "message": "An error occurred while changing the password. Please try again later.",
            },
        )
