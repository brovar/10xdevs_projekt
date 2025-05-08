import os
import aiofiles
from fastapi import UploadFile, HTTPException, status
from uuid import uuid4
from PIL import Image
import io
from logging import Logger
import shutil

# Stałe
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
UPLOAD_DIR = "uploads/offers"

# Upewniamy się, że katalog na pliki istnieje
os.makedirs(UPLOAD_DIR, exist_ok=True)

class FileService:
    def __init__(self, logger: Logger):
        self.logger = logger
    
    async def validate_image(self, image: UploadFile) -> bytes:
        """
        Validates image file type and size.
        
        Args:
            image: The uploaded image file
            
        Returns:
            bytes: The image content
            
        Raises:
            HTTPException: If validation fails
        """
        if not image:
            return None
            
        # Read file content
        content = await image.read()
        
        # Validate file size
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "FILE_TOO_LARGE",
                    "message": "Image size exceeds the 5MB limit"
                }
            )
        
        # Validate file type
        if image.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_FILE_TYPE",
                    "message": "Unsupported image format. Use JPG, PNG or WebP"
                }
            )
        
        # Reset file cursor for future read operations
        await image.seek(0)
        
        return content
    
    async def save_image(self, image: UploadFile) -> str:
        """
        Validates and saves an image file.
        
        Args:
            image: The uploaded image file
            
        Returns:
            str: The saved image filename
            
        Raises:
            HTTPException: If validation or saving fails
        """
        try:
            if not image:
                return None
                
            # Validate the image
            content = await self.validate_image(image)
            
            # Generate unique filename
            ext = image.filename.split('.')[-1].lower()
            image_filename = f"{uuid4()}.{ext}"
            image_path = os.path.join(UPLOAD_DIR, image_filename)
            
            # Save the file
            async with aiofiles.open(image_path, 'wb') as out_file:
                await out_file.write(content)
                
            return image_filename
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"File upload error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "FILE_UPLOAD_FAILED",
                    "message": "Failed to upload the image"
                }
            ) 