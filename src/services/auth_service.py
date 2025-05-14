import traceback
from logging import Logger

from fastapi import HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models import LogModel, UserModel
from schemas import (LogEventType, LoginUserRequest, RegisterUserRequest,
                     UserStatus)
from utils.password_utils import get_password_hash, verify_password

from .session_service import SessionService
from .validation_service import ValidationService


class AuthServiceError(Exception):
    """Base exception for auth service errors"""

    def __init__(self, error_code: str, message: str, status_code: int = 500):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthService:
    def __init__(
        self,
        db_session: AsyncSession,
        logger: Logger,
        session_service: SessionService,
    ):
        self.db_session = db_session
        self.logger = logger
        self.session_service = session_service
        self.validation_service = ValidationService()

    async def register_user(
        self, register_data: RegisterUserRequest, request: Request
    ) -> UserModel:
        """
        Register a new user with the provided data.

        Args:
            register_data: Registration data including email, password, and role
            request: FastAPI request object for logging IP

        Returns:
            UserModel: The created user model

        Raises:
            AuthServiceError: If registration fails
        """
        try:
            # Normalize email
            normalized_email = self.validation_service.normalize_email(
                register_data.email
            )

            # Validate password
            is_valid_password, validation_details = (
                self.validation_service.validate_password(
                    register_data.password
                )
            )

            if not is_valid_password:
                error_message = (
                    self.validation_service.get_password_error_message(
                        validation_details
                    )
                )
                raise AuthServiceError(
                    error_code="INVALID_PASSWORD",
                    message=error_message,
                    status_code=400,
                )

            # Check if user with this email already exists
            user_result = await self.db_session.execute(
                select(UserModel).where(UserModel.email == normalized_email)
            )
            existing_user = user_result.scalars().first()

            if existing_user:
                raise AuthServiceError(
                    error_code="EMAIL_ALREADY_EXISTS",
                    message="User with this email already exists.",
                    status_code=400,
                )

            # Log password strength for educational purposes
            self.logger.info(
                f"Password strength for new user {normalized_email}: {validation_details['strength']}"
            )

            # Hash the password
            password_hash = get_password_hash(register_data.password)

            # Create new user
            new_user = UserModel(
                email=normalized_email,
                password_hash=password_hash,
                role=register_data.role,
                status=UserStatus.ACTIVE,
                first_name=None,
                last_name=None,
            )

            self.db_session.add(new_user)

            # Log registration attempt
            log_entry = LogModel(
                event_type=LogEventType.USER_REGISTER,
                ip_address=request.client.host,
                message=f"User registration: {normalized_email} with role {register_data.role.value}",
            )
            self.db_session.add(log_entry)

            try:
                await self.db_session.commit()

                # Update log with user_id now that we have it
                log_entry.user_id = new_user.id
                log_entry.message += f", assigned ID: {new_user.id}"
                await self.db_session.commit()

                return new_user
            except IntegrityError:
                await self.db_session.rollback()
                self.logger.error(
                    f"Integrity error while registering user {normalized_email}"
                )
                raise AuthServiceError(
                    error_code="EMAIL_ALREADY_EXISTS",
                    message="User with this email already exists.",
                    status_code=400,
                )
            except Exception as e:
                await self.db_session.rollback()
                self.logger.error(
                    f"Failed to commit user registration: {str(e)}"
                )
                self.logger.debug(traceback.format_exc())
                raise AuthServiceError(
                    error_code="REGISTRATION_FAILED",
                    message="An error occurred during registration. Please try again later.",
                    status_code=500,
                )

        except AuthServiceError:
            # Re-raise auth service errors
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error during registration: {str(e)}"
            )
            self.logger.debug(traceback.format_exc())
            raise AuthServiceError(
                error_code="REGISTRATION_FAILED",
                message="An unexpected error occurred during registration. Please try again later.",
                status_code=500,
            )

    async def login_user(
        self,
        login_data: LoginUserRequest,
        request: Request,
        response: Response,
    ) -> bool:
        """
        Authenticate a user based on email and password and create a session.

        Args:
            login_data: The login request data containing email and password
            request: The FastAPI request object
            response: The FastAPI response object

        Returns:
            bool: True if authentication is successful

        Raises:
            AuthServiceError: With specific error codes for different failure scenarios
        """
        try:
            # Normalize email
            normalized_email = self.validation_service.normalize_email(
                login_data.email
            )

            # Find user by email
            user_result = await self.db_session.execute(
                select(UserModel).where(UserModel.email == normalized_email)
            )
            user = user_result.scalars().first()

            # Log attempt
            log_message = f"Login attempt for email {normalized_email}"
            event_type = LogEventType.USER_LOGIN

            # Verify credentials and user status
            if not user:
                # Don't expose that user doesn't exist
                log_entry = LogModel(
                    event_type=event_type,
                    ip_address=request.client.host,
                    message=f"{log_message}: user not found",
                )
                self.db_session.add(log_entry)
                await self.db_session.commit()

                raise AuthServiceError(
                    error_code="INVALID_CREDENTIALS",
                    message="Invalid login credentials.",
                    status_code=401,
                )

            # Add user_id to log now that we have it
            log_entry = LogModel(
                event_type=event_type,
                user_id=user.id,
                ip_address=request.client.host,
                message=log_message,
            )

            # Check if password is correct
            if not verify_password(login_data.password, user.password_hash):
                log_entry.message += ": invalid password"
                self.db_session.add(log_entry)
                await self.db_session.commit()

                raise AuthServiceError(
                    error_code="INVALID_CREDENTIALS",
                    message="Invalid login credentials.",
                    status_code=401,
                )

            # Check if user is active
            if user.status != "Active":
                log_entry.message += f": user inactive (status={user.status})"
                self.db_session.add(log_entry)
                await self.db_session.commit()

                raise AuthServiceError(
                    error_code="USER_INACTIVE",
                    message="User account is inactive.",
                    status_code=401,
                )

            try:
                # Update log message for successful login
                log_entry.message += ": successful"
                self.db_session.add(log_entry)

                # Verify session_service is available and properly initialized
                if self.session_service is None:
                    self.logger.error(
                        "Session service is None in login_user method"
                    )
                    raise AuthServiceError(
                        error_code="SESSION_CREATION_FAILED",
                        message="An error occurred while creating the session. Please try again later.",
                        status_code=500,
                    )

                # Check that create_session method exists and is callable
                if not hasattr(
                    self.session_service, "create_session"
                ) or not callable(self.session_service.create_session):
                    self.logger.error(
                        "Session service doesn't have a callable create_session method"
                    )
                    raise AuthServiceError(
                        error_code="SESSION_CREATION_FAILED",
                        message="An error occurred while creating the session. Please try again later.",
                        status_code=500,
                    )

                # Create session with detailed logging
                self.logger.info(
                    f"Creating session for user {user.id} with role {user.role.value}"
                )
                try:
                    await self.session_service.create_session(
                        response=response,
                        user_id=user.id,
                        user_role=user.role.value,
                    )
                    self.logger.info(
                        f"Session created successfully for user {user.id}"
                    )
                except Exception as session_error:
                    self.logger.error(
                        f"Error creating session: {str(session_error)}"
                    )
                    self.logger.error(f"Error type: {type(session_error)}")
                    self.logger.error(
                        f"Session service: {self.session_service}"
                    )
                    self.logger.error(
                        f"Session methods: {dir(self.session_service)}"
                    )
                    raise AuthServiceError(
                        error_code="SESSION_CREATION_FAILED",
                        message="An error occurred while creating the session. Please try again later.",
                        status_code=500,
                    )

                await self.db_session.commit()
                return True
            except AuthServiceError:
                # Re-raise auth service errors
                raise
            except Exception as e:
                await self.db_session.rollback()
                self.logger.error(f"Failed to process login: {str(e)}")
                self.logger.debug(traceback.format_exc())
                raise AuthServiceError(
                    error_code="SESSION_CREATION_FAILED",
                    message="An error occurred while creating the session. Please try again later.",
                    status_code=500,
                )
        except AuthServiceError:
            # Re-raise auth service errors
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during login: {str(e)}")
            self.logger.debug(traceback.format_exc())
            raise AuthServiceError(
                error_code="LOGIN_FAILED",
                message="An unexpected error occurred during login. Please try again later.",
                status_code=500,
            )

    async def logout_user(self, request: Request, response: Response) -> bool:
        """
        Log out a user by ending their session and logging the event.

        Returns 200 OK even if the user was not logged in to begin with.

        Args:
            request: FastAPI request object
            response: FastAPI response object

        Returns:
            bool: True if logout was successful or user wasn't logged in

        Raises:
            AuthServiceError: Only if there's a server error during logout
        """
        try:
            # Try to get session data, but don't fail if not authenticated
            try:
                session_data = await self.session_service.get_session(request)
                user_id = session_data.user_id
                is_authenticated = True
            except HTTPException:
                # User wasn't logged in - that's fine for logout
                user_id = None
                is_authenticated = False

            # If user was authenticated, end session and log the event
            if is_authenticated:
                # End the session
                session_ended = await self.session_service.end_session(
                    response, request=request
                )

                if not session_ended:
                    self.logger.warning("Failed to end session during logout")

                # Log the logout event
                try:
                    log_entry = LogModel(
                        event_type=LogEventType.USER_LOGIN,  # Use the same event type as login
                        user_id=user_id,
                        ip_address=request.client.host,
                        message=f"User {user_id} logged out successfully",
                    )

                    self.db_session.add(log_entry)
                    await self.db_session.commit()
                except Exception as e:
                    # Non-critical error - just log it but don't fail the logout
                    await self.db_session.rollback()
                    self.logger.error(f"Failed to log logout event: {str(e)}")
                    self.logger.debug(traceback.format_exc())
            else:
                # Just make sure any cookies are cleared
                try:
                    await self.session_service.end_session(
                        response, request=request
                    )
                except Exception as e:
                    self.logger.debug(
                        f"Non-critical error during logout of unauthenticated user: {str(e)}"
                    )

            return True
        except Exception as e:
            self.logger.error(f"Failed to process logout: {str(e)}")
            self.logger.debug(traceback.format_exc())
            raise AuthServiceError(
                error_code="LOGOUT_FAILED",
                message="An error occurred during logout. Please try again later.",
                status_code=500,
            )
