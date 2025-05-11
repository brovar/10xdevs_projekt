import logging
import os
from logging import Logger
from typing import AsyncGenerator, Callable, Dict, List, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from schemas import UserRole
from services.auth_service import AuthService
from services.log_service import LogService
from services.order_service import OrderService
from services.session_service import SessionService
from services.user_service import UserService

# Database connection setup
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/steambay",
)
# Fallback to localhost if using local development
if (
    "postgres:5432" in DATABASE_URL
    and os.environ.get("ENVIRONMENT") != "docker"
):
    DATABASE_URL = DATABASE_URL.replace("postgres:5432", "localhost:5432")

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create a single session service instance with properly set parameters
session_service = SessionService(
    cookie_name="steambay_session",
    cookie_max_age=604800,  # 7 days
    secret_key=os.environ.get(
        "SESSION_SECRET", "INSECURE_SECRET_KEY_CHANGE_IN_PRODUCTION"
    ),
)

# Security
security = HTTPBearer()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for database session.

    Yields:
        AsyncSession: The SQLAlchemy async session
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_logger() -> Logger:
    """
    Dependency for logger.

    Returns:
        Logger: Application logger
    """
    return logging.getLogger("steambay")


def get_session_service() -> SessionService:
    """
    Dependency for session service.

    Returns:
        SessionService: The session service
    """
    return session_service


async def require_authenticated(
    request: Request,
    session_service: SessionService = Depends(get_session_service),
) -> Dict[str, any]:
    """
    Dependency that checks if user is authenticated.

    Args:
        request: FastAPI request object
        session_service: Session service for checking authentication

    Returns:
        dict: User session data including user_id and user_role

    Raises:
        HTTPException: 401 Unauthorized if user is not authenticated
    """
    try:
        session_data = await session_service.get_session(request)
        return {
            "user_id": session_data.user_id,
            "user_role": session_data.user_role,
        }
    except HTTPException:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "NOT_AUTHENTICATED",
                "message": "Użytkownik nie jest zalogowany.",
            },
        )


def require_roles(allowed_roles: List[UserRole]) -> Callable:
    """
    Factory for creating role-based access control dependencies.

    Args:
        allowed_roles: List of roles that are allowed to access the endpoint

    Returns:
        Callable: Dependency function that checks if the user has one of the allowed roles
    """

    async def role_dependency(
        user_data: Dict = Depends(require_authenticated),
    ) -> Dict:
        user_role = user_data.get("user_role")

        # Convert to UserRole enum if it's a string
        if isinstance(user_role, str):
            try:
                user_role = UserRole(user_role)
            except ValueError:
                # If the role string doesn't match any enum value
                user_role = None

        if not user_role or user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                    "message": "Nie masz uprawnień do wykonania tej operacji.",
                },
            )

        return user_data

    return role_dependency


# Common role-based dependencies
require_admin = require_roles([UserRole.ADMIN])
require_seller = require_roles([UserRole.SELLER, UserRole.ADMIN])
require_buyer_or_seller = require_roles(
    [UserRole.BUYER, UserRole.SELLER, UserRole.ADMIN]
)


# Service dependencies for DI
def get_order_service(
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
) -> OrderService:
    """Dependency that provides an OrderService instance."""
    return OrderService(db_session, logger)


def get_log_service(
    db_session: AsyncSession = Depends(get_db_session),
) -> LogService:
    """Dependency that provides a LogService instance."""
    return LogService(db_session)


def get_user_service(
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
) -> "UserService":
    """Dependency that provides a UserService instance."""
    from services.user_service import UserService

    return UserService(db_session, logger)


def get_payment_service(
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
) -> "PaymentService":
    """Dependency that provides a PaymentService instance."""
    from services.payment_service import PaymentService

    return PaymentService(db_session, logger)


def get_offer_service(
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
) -> "OfferService":
    """Dependency that provides an OfferService instance."""
    from services.offer_service import OfferService

    return OfferService(db_session, logger)


def get_media_service(logger: Logger = Depends(get_logger)) -> "MediaService":
    """Dependency that provides a MediaService instance."""
    from services.media_service import MediaService

    return MediaService(logger)


def get_auth_service(
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
    session_service: SessionService = Depends(get_session_service),
) -> AuthService:
    """Dependency that provides an AuthService instance."""
    return AuthService(db_session, logger, session_service)


# Aliases for backward compatibility
require_auth = require_authenticated


def require_role(required_role: UserRole):
    """
    Alias factory for requiring a single role for backward compatibility.
    """
    return require_roles([required_role])


async def get_current_user_optional(
    request: Request,
    session_service: SessionService = Depends(get_session_service),
) -> Optional[Dict[str, any]]:
    """
    Dependency that gets the current user if authenticated, but doesn't raise an exception if not.

    Args:
        request: FastAPI request object
        session_service: Session service for checking authentication

    Returns:
        Optional[dict]: User session data if authenticated, None otherwise
    """
    try:
        session_data = await session_service.get_session(request)
        return {
            "user_id": session_data.user_id,
            "user_role": session_data.user_role,
        }
    except HTTPException:
        return None


# Removed the incorrect require_role definition as it was causing NameError
# The require_roles factory function should be used instead
# async def require_role(required_role: UserRole, current_user: UserModel = Depends(require_authenticated)):
#     # Implementation of require_role function was likely incorrect
#     pass
