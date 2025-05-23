import traceback
from logging import Logger

from fastapi import (APIRouter, Depends, HTTPException, Request, Response,
                     status)
from fastapi.responses import JSONResponse
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from dependencies import (get_auth_service, get_db_session, get_logger,
                          get_session_service)
from models import UserModel
from schemas import (LoginUserRequest, LoginUserResponse, LogoutUserResponse,
                     RegisterUserRequest, RegisterUserResponse)
from services.auth_service import AuthService, AuthServiceError
from services.session_service import SessionService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterUserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User successfully registered"},
        400: {
            "description": "Invalid input, email already exists, or password doesn't meet requirements",
            "content": {
                "application/json": {
                    "examples": {
                        "EMAIL_ALREADY_EXISTS": {
                            "summary": "Email already exists",
                            "value": {
                                "error_code": "EMAIL_ALREADY_EXISTS",
                                "message": "Użytkownik o podanym adresie email już istnieje.",
                            },
                        },
                        "INVALID_PASSWORD": {
                            "summary": "Password doesn't meet requirements",
                            "value": {
                                "error_code": "PASSWORD_POLICY_VIOLATED",
                                "message": "Password must contain at least 10 characters, an uppercase letter, and a lowercase letter.",
                            },
                        },
                        "INVALID_INPUT": {
                            "summary": "Invalid input data",
                            "value": {
                                "error_code": "INVALID_INPUT",
                                "message": "Invalid request data",
                                "detail": "Field errors...",
                            },
                        },
                    }
                }
            },
        },
        500: {"description": "Server error during registration process"},
    },
)
async def register_user(
    register_data: RegisterUserRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    logger: Logger = Depends(get_logger),
):
    """
    Register a new user.

    This endpoint creates a new user account with the provided details.

    ## Input Fields
    - **email**: Valid email address (required)
    - **password**: Password that meets the security requirements (required)
    - **role**: User role, either "Buyer" or "Seller" (required)

    ## Password Requirements
    For educational purposes, the password should meet at least 3 of these criteria:
    - At least 10 characters long
    - Contains at least one uppercase letter (A-Z)
    - Contains at least one lowercase letter (a-z)
    - Contains at least one digit (0-9) or special character (!@#$%^&*(),.?":{}|<>)

    ## Response
    Returns the created user details on success, including:
    - User ID
    - Email address
    - Role
    - Status
    - Creation timestamp

    ## Error Codes
    - **EMAIL_ALREADY_EXISTS**: A user with this email address already exists
    - **INVALID_PASSWORD**: Password doesn't meet the security requirements
    - **INVALID_INPUT**: One or more input fields are invalid
    - **REGISTRATION_FAILED**: Server error during registration

    ## Educational Notes
    This is an educational application, so:
    - Email addresses are not verified
    - Password requirements are meant to demonstrate good practices
    - In a production environment, additional security measures would be implemented
    """
    try:
        # Log registration request details (without sensitive data)
        if logger:
            logger.info(
                f"Registration request: email={register_data.email}, role={register_data.role}"
            )

        # Register the user
        new_user = await auth_service.register_user(register_data, request)

        # Log success
        if logger:
            logger.info(
                f"User registered successfully: id={new_user.id}, email={new_user.email}, role={new_user.role}"
            )

        # Return user details without password
        return {
            "id": new_user.id,
            "email": new_user.email,
            "role": new_user.role,
            "status": new_user.status,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "created_at": new_user.created_at,
        }
    except AuthServiceError as e:
        if logger:
            logger.error(
                f"AuthServiceError during registration: {e.error_code} - {e.message}"
            )
        return JSONResponse(
            status_code=e.status_code,
            content={"error_code": e.error_code, "message": e.message},
        )
    except Exception as e:
        # Get full traceback for debugging
        error_traceback = traceback.format_exc()
        if logger:
            logger.error(f"Unexpected error during registration: {str(e)}")
            logger.error(f"Traceback: {error_traceback}")
            logger.error(
                f"Request data: {register_data.dict(exclude={'password'})}"
            )

        return JSONResponse(
            status_code=500,
            content={
                "error_code": "REGISTRATION_FAILED",
                "message": "An unexpected error occurred during registration. Please try again later.",
                "debug_info": str(e) if logger else None,
            },
        )


@router.post(
    "/login",
    response_model=LoginUserResponse,
    responses={
        200: {"description": "Successfully authenticated"},
        401: {
            "description": "Authentication failed due to invalid credentials or inactive user"
        },
        500: {"description": "Server error during login process"},
    },
)
async def login_user(
    login_data: LoginUserRequest,
    response: Response,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    logger: Logger = Depends(get_logger),
    csrf_protect: CsrfProtect = Depends(),
):
    """
    Authenticate a user and create a session.

    This endpoint validates user credentials and establishes a session by setting
    an HttpOnly Secure cookie. The cookie is used for subsequent authenticated requests.

    - **email**: User's email address (required)
    - **password**: User's password (required)

    Returns a success message on successful authentication.

    Various error codes may be returned:
    - INVALID_CREDENTIALS: Email or password is incorrect
    - USER_INACTIVE: User account is not active
    - LOGIN_FAILED: Server error during login
    - SESSION_CREATION_FAILED: Error creating the user session
    """
    try:
        # Use the auth service to handle login
        await auth_service.login_user(login_data, request, response)

        # Set CSRF token in cookie - using a try/except to handle potential errors
        try:
            csrf_protect.set_csrf_cookie(response)
        except Exception as csrf_error:
            logger.warning(f"CSRF cookie could not be set: {str(csrf_error)}")
            # Continue despite CSRF error - this will allow login but CSRF protection may not work

        return {"message": "Login successful"}
    except AuthServiceError as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error_code": e.error_code, "message": e.message},
        )
    except Exception as e:
        if logger:
            logger.error(f"Unexpected error during login: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "LOGIN_FAILED",
                "message": "An unexpected error occurred during login. Please try again later.",
            },
        )


@router.post(
    "/logout",
    response_model=LogoutUserResponse,
    responses={
        200: {
            "description": "Successfully logged out or user wasn't logged in"
        },
        403: {"description": "CSRF token missing or invalid"},
        500: {"description": "Server error during logout process"},
    },
)
async def logout_user(
    request: Request,
    response: Response,
    csrf_protect: CsrfProtect = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    logger: Logger = Depends(get_logger),
):
    """
    End a user's session (logout).

    This endpoint terminates the user's session by clearing the session cookie.
    It always returns a 200 OK response, even if the user wasn't logged in.

    CSRF protection is required for this endpoint:
    - The request must include a valid CSRF token in the X-CSRF-Token header
    - The token must match the one stored in the csrf_token cookie

    Returns a success message indicating logout was successful.

    Error codes that may be returned:
    - INVALID_CSRF: The CSRF token is missing or invalid
    - LOGOUT_FAILED: Server error during logout process
    """
    try:
        # Validate CSRF token
        try:
            csrf_protect.validate_csrf(request)
        except Exception as csrf_error:
            logger.warning(
                f"CSRF validation failed during logout: {str(csrf_error)}"
            )
            # For logout, we'll still allow the operation to proceed
            # This provides better UX while marginally reducing security
            logger.info(
                "Proceeding with logout despite CSRF validation failure"
            )

        # Log out user - handles both authenticated and unauthenticated users
        await auth_service.logout_user(request, response)
        return {"message": "Logout successful"}
    except AuthServiceError as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error_code": e.error_code, "message": e.message},
        )
    except Exception as e:
        if logger:
            logger.error(f"Unexpected error during logout: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "LOGOUT_FAILED",
                "message": "An unexpected error occurred during logout. Please try again later.",
            },
        )


@router.get(
    "/status",
    responses={
        200: {
            "description": "Returns current authentication status and user info if authenticated"
        },
        500: {"description": "Server error while checking status"},
    },
)
async def auth_status(
    request: Request,
    session_service: SessionService = Depends(get_session_service),
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """
    Get the current authentication status and user information.

    This endpoint returns:
    - is_authenticated: Whether the user is currently authenticated
    - user: User information if authenticated (null otherwise)

    No authentication is required to call this endpoint.
    """
    try:
        # Try to get session data
        try:
            session_data = await session_service.get_session(request)
            is_authenticated = True

            # Query for user details
            user_id = session_data.user_id
            user_role = session_data.user_role

            logger.info(f"User authenticated: ID={user_id}, role={user_role}")

            # Get extended user info from database
            user_result = await db.execute(
                select(UserModel).where(UserModel.id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning(
                    f"User ID {user_id} from session not found in database"
                )
                # Session exists but user doesn't - this is unusual
                # Return minimal info from session only
                user_info = {
                    "id": user_id,
                    "user_id": user_id,  # Add both formats for compatibility with frontend
                    "role": user_role,
                    "email": "unknown@user.com",  # Placeholder
                }
            else:
                # Return full user info
                user_info = {
                    "id": str(user.id),
                    "user_id": str(
                        user.id
                    ),  # Add both formats for compatibility with frontend
                    "email": user.email,
                    "role": user.role,
                    "status": user.status,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "created_at": user.created_at,
                }
        except HTTPException:
            # Not authenticated
            is_authenticated = False
            user_info = None
            logger.info("No active session found")

        return {"is_authenticated": is_authenticated, "user": user_info}
    except Exception as e:
        logger.error(f"Error checking auth status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "STATUS_CHECK_FAILED",
                "message": "An error occurred while checking authentication status.",
            },
        )


@router.post(
    "/refresh-csrf",
    responses={
        200: {"description": "Successfully refreshed CSRF token"},
        500: {"description": "Server error during CSRF token refresh"},
    },
)
async def refresh_csrf_token(
    response: Response,
    csrf_protect: CsrfProtect = Depends(),
    logger: Logger = Depends(get_logger),
):
    """
    Refresh the CSRF token.

    This endpoint generates a new CSRF token and sets it in the response cookie.
    Use this endpoint if your CSRF token is missing or has expired.

    Returns a success message indicating the token was refreshed.
    """
    try:
        # Set a new CSRF token
        csrf_protect.set_csrf_cookie(response)
        return {"message": "CSRF token refreshed successfully"}
    except Exception as e:
        logger.error(f"Error refreshing CSRF token: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "CSRF_REFRESH_FAILED",
                "message": "Failed to refresh CSRF token",
            },
        )
