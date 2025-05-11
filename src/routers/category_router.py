from logging import Logger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db_session, get_logger, require_authenticated
from schemas import CategoriesListResponse, LogEventType
from services.category_service import CategoryService
from services.log_service import LogService

router = APIRouter(tags=["categories"])


@router.get(
    "/categories",
    response_model=CategoriesListResponse,
    responses={
        200: {"description": "Successfully retrieved categories list"},
        401: {
            "description": "User is not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "NOT_AUTHENTICATED",
                        "message": "Użytkownik nie jest zalogowany.",
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
                        "message": "Failed to retrieve category data",
                    }
                }
            },
        },
    },
)
async def list_categories(
    request: Request,
    session_data: dict = Depends(require_authenticated),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """
    Get all available product categories.

    This endpoint returns a list of all categories available in the system.
    Categories are used to classify product offers.

    ## Response
    Returns a list of categories, each with:
    - id: Unique identifier for the category
    - name: Display name of the category

    ## Authentication
    This endpoint requires user authentication.

    ## Error Codes
    - NOT_AUTHENTICATED: User is not logged in
    - FETCH_FAILED: Server error occurred while retrieving categories
    """
    try:
        # Get user ID from session for logging
        user_id = session_data.get("user_id")
        user_email = session_data.get(
            "email", "unknown_user"
        )  # Get email for logging, provide default

        # Call service to get categories
        category_service = CategoryService(db_session, logger)
        categories = await category_service.get_all_categories()

        # Initialize log service
        log_service = LogService(db_session)

        # Log the action
        await log_service.create_log(
            event_type=LogEventType.CATEGORY_LIST_VIEWED,
            message=f"User {user_email} viewed categories list",
            user_id=UUID(user_id) if user_id else None,
        )

        # Return categories list response
        return CategoriesListResponse(items=categories)
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Initialize log service
        log_service = LogService(db_session)

        # Log error with user id if available from session_data
        user_id_for_log = session_data.get("user_id") if session_data else None
        await log_service.create_log(
            event_type=LogEventType.ADMIN_ACTION_FAIL,
            message=f"Error fetching categories: {str(e)}",
            user_id=UUID(user_id_for_log) if user_id_for_log else None,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "FETCH_FAILED",
                "message": "Failed to retrieve category data",
            },
        )
