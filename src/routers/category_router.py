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
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error_code": "FETCH_FAILED",
                            "message": "Failed to retrieve category data",
                        }
                    }
                }
            },
        },
    },
)
async def list_categories(
    request: Request,
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
) -> CategoriesListResponse:
    """
    List all available categories
    """
    try:
        # Create category service
        category_service = CategoryService(db_session)
        
        # Get all categories
        categories = await category_service.list_categories()
        
        # Add log entry (without requiring authentication)
        try:
            log_service = LogService(db_session)
            await log_service.create_log(
                user_id=None,  # Anonymous user
                event_type=LogEventType.CATEGORY_LIST_VIEWED,
                message="Categories list viewed",
                ip_address=request.client.host if request.client else None,
            )
        except Exception as log_error:
            # If logging fails, just log the error but don't fail the request
            logger.error(f"Failed to log category list view: {str(log_error)}")
        
        return {"items": categories}
    except Exception as e:
        # Log the error
        logger.error(f"Failed to retrieve category data: {str(e)}")
        
        # Return a meaningful error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "FETCH_FAILED",
                "message": "Failed to retrieve category data",
            },
        )
