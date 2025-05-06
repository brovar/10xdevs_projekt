from fastapi import APIRouter, Depends, HTTPException, status, Path, Response, Request, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from logging import Logger

from dependencies import get_db_session, get_logger, get_media_service
from models import OfferModel
from services.media_service import MediaService
from services.auth import get_current_user_optional
from schemas import UserRole
from exceptions.offer_exceptions import OfferNotFoundException

router = APIRouter(prefix="/media", tags=["media"])

@router.get("/offers/{offer_id}/{filename}")
async def get_offer_image(
    offer_id: UUID = Path(..., description="UUID of the offer"),
    filename: str = Path(..., description="Filename of the image"),
    current_user = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
    media_service: MediaService = Depends(lambda: MediaService(logger))
):
    """
    Get an image file associated with an offer.
    
    - Public access for 'active' offers
    - Restricted access for other offer statuses (owner, admin)
    - Returns the image file with appropriate headers
    """
    try:
        # Get offer from database
        offer = await db.get(OfferModel, offer_id)
        
        # Check if offer exists
        if not offer:
            raise OfferNotFoundException(offer_id)
        
        # Extract user information if authenticated
        current_user_id = current_user.id if current_user else None
        current_user_role = current_user.role if current_user else None
        
        # Check access permission
        await media_service.check_offer_image_access(
            offer,
            current_user_id,
            current_user_role
        )
        
        # Get validated file path
        file_path = await media_service.get_offer_image_path(
            offer_id,
            filename,
            offer
        )
        
        # Set cache control based on offer status
        cache_control = "public, max-age=3600" if offer.status == "active" else "no-store"
        
        # Return file response with appropriate headers
        return FileResponse(
            path=str(file_path),
            media_type="image/png",
            filename=filename,
            content_disposition_type="inline",
            headers={"Cache-Control": cache_control}
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (already handled in service)
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in get_offer_image endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "FILE_SERVE_FAILED",
                "message": "An unexpected error occurred"
            }
        ) 