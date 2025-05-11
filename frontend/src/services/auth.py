from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db_session
from models import UserModel

security = HTTPBearer()


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db_session)
):
    """
    Get the current authenticated user.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        User object for the authenticated user

    Raises:
        HTTPException: If user is not authenticated or not found
    """
    # This is a placeholder - actual implementation would verify JWT token
    # or session from the request and retrieve the user from DB

    token = request.headers.get("Authorization", "")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "NOT_AUTHENTICATED",
                "message": "Użytkownik nie jest zalogowany.",
            },
        )

    # In the real implementation, we would verify the token and extract user_id
    user_id = UUID("12345678-1234-5678-1234-567812345678")  # Placeholder

    # Get the user from database
    user = await db.get(UserModel, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "USER_NOT_FOUND",
                "message": "Nie znaleziono użytkownika.",
            },
        )

    return user


async def get_current_user_optional(
    request: Request, db: AsyncSession = Depends(get_db_session)
):
    """
    Similar to get_current_user but returns None instead of raising an exception
    if no user is authenticated

    Args:
        request: The FastAPI request object
        db: Database session

    Returns:
        User object if authenticated, None otherwise
    """
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
