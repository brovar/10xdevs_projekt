from fastapi import HTTPException, status
from pathlib import Path
import aiofiles
import os
import uuid
from typing import Optional
from logging import Logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from config import OFFER_IMAGES_DIR
from models import OfferModel, LogModel
from schemas import OfferStatus, UserRole, LogEventType
from exceptions.offer_exceptions import OfferNotFoundException

class MediaService:
    def __init__(self, logger: Logger):
        self.logger = logger
    
    async def get_offer_image_path(
        self,
        offer_id: uuid.UUID,
        filename: str,
        offer: Optional[OfferModel] = None
    ) -> Path:
        """
        Validate and return the path to an offer image file
        
        Args:
            offer_id: UUID of the offer
            filename: Name of the image file
            offer: Optional Offer object if already fetched
            
        Returns:
            Path object pointing to the image file
            
        Raises:
            HTTPException: If the path is invalid or file doesn't exist
        """
        # Sanitize filename to prevent path traversal
        safe_filename = os.path.basename(filename)
        
        # Ensure filename doesn't start with dots or contain suspicious patterns
        if safe_filename != filename or ".." in filename or filename.startswith("."):
            self.logger.warning(f"Attempted path traversal: {filename}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_FILENAME",
                    "message": "Invalid filename"
                }
            )
        
        # Construct file path
        file_path = OFFER_IMAGES_DIR / str(offer_id) / safe_filename
        
        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            self.logger.info(f"Image not found: {file_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "IMAGE_NOT_FOUND",
                    "message": "Image file not found"
                }
            )
        
        return file_path
    
    async def check_offer_image_access(
        self,
        offer: OfferModel,
        current_user_id: Optional[uuid.UUID] = None,
        current_user_role: Optional[UserRole] = None
    ) -> bool:
        """
        Check if user has access to the offer image
        
        Args:
            offer: The offer object
            current_user_id: Optional UUID of the current user
            current_user_role: Optional role of the current user
            
        Returns:
            True if access is allowed, otherwise raises HTTPException
            
        Raises:
            HTTPException: If access is denied
        """
        # Public access for active offers
        if offer.status == OfferStatus.ACTIVE:
            return True
        
        # For non-active offers, user must be authenticated
        if current_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "NOT_AUTHENTICATED",
                    "message": "Authentication required to access this image"
                }
            )
        
        # Admin has access to all images
        if current_user_role == UserRole.ADMIN:
            return True
        
        # Seller has access to their own offers' images
        if offer.seller_id == current_user_id:
            return True
        
        # Access denied for all other cases
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "ACCESS_DENIED",
                "message": "You don't have permission to access this image"
            }
        )
    
    async def read_image_file(self, file_path: Path) -> bytes:
        """
        Read image file asynchronously
        
        Args:
            file_path: Path to the image file
            
        Returns:
            File content as bytes
            
        Raises:
            HTTPException: If file reading fails
        """
        try:
            async with aiofiles.open(file_path, "rb") as file:
                return await file.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "FILE_SERVE_FAILED",
                    "message": "Failed to serve the image file"
                }
            )

    async def update_offer_status(self, offer_id: UUID, new_status: OfferStatus, session: AsyncSession):
        """
        Update the status of an offer
        
        Args:
            offer_id: UUID of the offer
            new_status: The new status for the offer
            session: The database session
            
        Returns:
            Updated offer object
            
        Raises:
            HTTPException: If the update fails
        """
        try:
            # Construct the query to update the offer status
            query = update(OfferModel).where(OfferModel.id == offer_id).values(status=new_status)
            
            # Execute the query
            result = await session.execute(query)
            
            # Commit the transaction
            await session.commit()
            
            # Return the updated offer
            return result.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating offer status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "OFFER_STATUS_UPDATE_FAILED",
                    "message": "Failed to update offer status"
                }
            )

    async def log_offer_status_change(self, offer_id: UUID, new_status: OfferStatus, event_type: LogEventType, session: AsyncSession):
        """
        Log the change in offer status
        
        Args:
            offer_id: UUID of the offer
            new_status: The new status for the offer
            event_type: The type of event for the log
            session: The database session
            
        Returns:
            True if the log was successful, otherwise False
            
        Raises:
            HTTPException: If the log fails
        """
        try:
            # Create a new LogModel instance
            log = LogModel(
                offer_id=offer_id,
                status=new_status,
                event_type=event_type
            )
            
            # Add the log to the session
            session.add(log)
            
            # Commit the transaction
            await session.commit()
            
            return True
        except Exception as e:
            self.logger.error(f"Error logging offer status change: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "OFFER_STATUS_LOG_FAILED",
                    "message": "Failed to log offer status change"
                }
            ) 