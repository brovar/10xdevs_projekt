from fastapi import HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from logging import Logger
from models import LogModel, UserModel
from schemas import LogEventType, LoginUserRequest, RegisterUserRequest, UserStatus
from services.session_service import SessionService
from services.validation_service import ValidationService, ValidationError
from utils.password_utils import verify_password, get_password_hash
from sqlalchemy import select, update, insert, delete
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import traceback

class AuthServiceError(Exception):
    """Base exception for auth service errors"""
    def __init__(self, error_code: str, message: str, status_code: int = 500):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class AuthService:
    def __init__(self, db_session: AsyncSession, logger: Logger, session_service: SessionService):
        self.db_session = db_session
        self.logger = logger
        self.session_service = session_service
        self.validation_service = ValidationService()
        
    async def register_user(self, register_data: RegisterUserRequest, request: Request) -> UserModel:
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
            # Log the registration data for debugging (excluding password)
            self.logger.debug(f"Registration request: email={register_data.email}, role={register_data.role}")
            
            # Validate role explicitly
            if not self.validation_service.validate_user_role(register_data.role):
                self.logger.error(f"Invalid role: {register_data.role}")
                raise AuthServiceError(
                    error_code="INVALID_ROLE",
                    message=f"Nieprawidłowa rola użytkownika: {register_data.role}. Dozwolone wartości to: Buyer, Seller.",
                    status_code=400
                )
                
            # Normalize email
            normalized_email = self.validation_service.normalize_email(register_data.email)
            
            # Validate password
            is_valid_password, validation_details = self.validation_service.validate_password(register_data.password)
            
            if not is_valid_password:
                error_message = self.validation_service.get_password_error_message(validation_details)
                raise AuthServiceError(
                    error_code="INVALID_PASSWORD",
                    message=error_message,
                    status_code=400
                )
            
            # Check if user with this email already exists
            user_result = await self.db_session.execute(
                select(UserModel).where(UserModel.email == normalized_email)
            )
            existing_user = user_result.scalars().first()
            
            if existing_user:
                raise AuthServiceError(
                    error_code="EMAIL_ALREADY_EXISTS",
                    message="Użytkownik o podanym adresie email już istnieje.",
                    status_code=400
                )
            
            # Log password strength for educational purposes
            self.logger.info(f"Password strength for new user {normalized_email}: {validation_details['strength']}")
            
            # Hash the password
            password_hash = get_password_hash(register_data.password)
            
            # Create new user
            new_user = UserModel(
                email=normalized_email,
                password_hash=password_hash,
                role=register_data.role,
                status=UserStatus.ACTIVE,
                first_name=None,
                last_name=None
            )
            
            self.db_session.add(new_user)
            
            # Log registration attempt
            log_entry = LogModel(
                event_type=LogEventType.USER_REGISTER,
                ip_address=request.client.host,
                message=f"User registration: {normalized_email} with role {register_data.role}"
            )
            self.db_session.add(log_entry)
            
            try:
                await self.db_session.commit()
                
                # Update log with user_id now that we have it
                log_entry.user_id = new_user.id
                log_entry.message += f", assigned ID: {new_user.id}"
                await self.db_session.commit()
                
                self.logger.info(f"User registered successfully: id={new_user.id}, email={new_user.email}, role={new_user.role}")
                return new_user
            except IntegrityError as e:
                await self.db_session.rollback()
                self.logger.error(f"Integrity error while registering user {normalized_email}: {str(e)}")
                raise AuthServiceError(
                    error_code="EMAIL_ALREADY_EXISTS",
                    message="Użytkownik o podanym adresie email już istnieje.",
                    status_code=400
                )
            except Exception as e:
                await self.db_session.rollback()
                self.logger.error(f"Failed to commit user registration: {str(e)}")
                self.logger.debug(traceback.format_exc())
                raise AuthServiceError(
                    error_code="REGISTRATION_FAILED",
                    message="Wystąpił błąd podczas rejestracji. Spróbuj ponownie później.",
                    status_code=500
                )
                
        except AuthServiceError:
            # Re-raise auth service errors
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during registration: {str(e)}")
            self.logger.debug(traceback.format_exc())
            raise AuthServiceError(
                error_code="REGISTRATION_FAILED",
                message="Wystąpił nieoczekiwany błąd podczas rejestracji. Spróbuj ponownie później.",
                status_code=500
            )

    async def login_user(self, login_data: LoginUserRequest, request: Request, response: Response) -> bool:
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
            normalized_email = self.validation_service.normalize_email(login_data.email)
            
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
                    message=f"{log_message}: user not found"
                )
                self.db_session.add(log_entry)
                await self.db_session.commit()
                
                raise AuthServiceError(
                    error_code="INVALID_CREDENTIALS",
                    message="Nieprawidłowe dane logowania.",
                    status_code=401
                )
            
            # Add user_id to log now that we have it
            log_entry = LogModel(
                event_type=event_type,
                user_id=user.id,
                ip_address=request.client.host,
                message=log_message
            )
            
            # Check if password is correct
            if not verify_password(login_data.password, user.password_hash):
                log_entry.message += ": invalid password"
                self.db_session.add(log_entry)
                await self.db_session.commit()
                
                raise AuthServiceError(
                    error_code="INVALID_CREDENTIALS", 
                    message="Nieprawidłowe dane logowania.",
                    status_code=401
                )
            
            # Check if user is active
            if user.status != UserStatus.ACTIVE:
                log_entry.message += f": user inactive (status={user.status})"
                self.db_session.add(log_entry)
                await self.db_session.commit()
                
                raise AuthServiceError(
                    error_code="USER_INACTIVE",
                    message="Konto użytkownika jest nieaktywne.",
                    status_code=401
                )
            
            try:
                # Log user role for debugging
                self.logger.info(f"User role: {user.role}, type: {type(user.role)}")
                if hasattr(user.role, 'value'):
                    self.logger.info(f"User role value: {user.role.value}, type: {type(user.role.value)}")
                
                # Update log message for successful login
                log_entry.message += ": successful"
                self.db_session.add(log_entry)
                
                # Create session
                await self.session_service.create_session(
                    response=response, 
                    user_id=user.id, 
                    user_role=user.role.value if hasattr(user.role, 'value') else str(user.role)
                )
                
                await self.db_session.commit()
                return True
            except Exception as e:
                self.logger.error(f"Failed to process login: {str(e)}")
                self.logger.error(f"Exception type: {type(e)}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Rollback the transaction
                await self.db_session.rollback()
                
                raise AuthServiceError(
                    error_code="LOGIN_FAILED", 
                    message="Wystąpił nieoczekiwany błąd podczas logowania. Spróbuj ponownie później.",
                    status_code=500
                )
        except AuthServiceError:
            # Re-raise auth service errors
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during login: {str(e)}")
            self.logger.debug(traceback.format_exc())
            raise AuthServiceError(
                error_code="LOGIN_FAILED",
                message="Wystąpił nieoczekiwany błąd podczas logowania. Spróbuj ponownie później.",
                status_code=500
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
                session_ended = await self.session_service.end_session(response, request=request)
                
                if not session_ended:
                    self.logger.warning("Failed to end session during logout")
                
                # Log the logout event
                try:
                    log_entry = LogModel(
                        event_type=LogEventType.USER_LOGIN,  # Use the same event type as login
                        user_id=user_id,
                        ip_address=request.client.host,
                        message=f"User {user_id} logged out successfully"
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
                    await self.session_service.end_session(response, request=request)
                except Exception as e:
                    self.logger.debug(f"Non-critical error during logout of unauthenticated user: {str(e)}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to process logout: {str(e)}")
            self.logger.debug(traceback.format_exc())
            raise AuthServiceError(
                error_code="LOGOUT_FAILED",
                message="Wystąpił błąd podczas wylogowania. Spróbuj ponownie później.",
                status_code=500
            ) 