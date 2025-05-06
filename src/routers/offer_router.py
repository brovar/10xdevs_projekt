from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status, Request, Path
from sqlalchemy.ext.asyncio import AsyncSession
from logging import Logger
from decimal import Decimal
from typing import Optional, List
from fastapi_csrf_protect import CsrfProtect
from uuid import UUID

import logging
logger = logging.getLogger(__name__)

from dependencies import get_db_session, get_logger as get_logger_dependency, require_seller, get_offer_service, get_media_service
from services.offer_service import OfferService
from services.media_service import MediaService
from schemas import OfferSummaryDTO, OfferDetailDTO, UserRole, LogEventType
from services.log_service import LogService
from models import LogModel

router = APIRouter(tags=["offers"])

@router.post(
    "/offers",
    response_model=OfferSummaryDTO,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Successfully created the offer"},
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "examples": {
                        "INVALID_INPUT": {
                            "summary": "Missing or invalid fields",
                            "value": {"error_code": "INVALID_INPUT", "message": "Invalid request data"}
                        },
                        "INVALID_PRICE": {
                            "summary": "Invalid price",
                            "value": {"error_code": "INVALID_PRICE", "message": "Price must be greater than 0"}
                        },
                        "INVALID_QUANTITY": {
                            "summary": "Invalid quantity",
                            "value": {"error_code": "INVALID_QUANTITY", "message": "Quantity cannot be negative"}
                        },
                        "INVALID_FILE_TYPE": {
                            "summary": "Invalid image format",
                            "value": {"error_code": "INVALID_FILE_TYPE", "message": "Unsupported image format. Use JPG, PNG or WebP"}
                        },
                        "FILE_TOO_LARGE": {
                            "summary": "Image too large",
                            "value": {"error_code": "FILE_TOO_LARGE", "message": "Image size exceeds the 5MB limit"}
                        }
                    }
                }
            }
        },
        401: {
            "description": "User not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "NOT_AUTHENTICATED",
                        "message": "Użytkownik nie jest zalogowany."
                    }
                }
            }
        },
        403: {
            "description": "User not authorized",
            "content": {
                "application/json": {
                    "examples": {
                        "INSUFFICIENT_PERMISSIONS": {
                            "summary": "Not a seller",
                            "value": {"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Nie masz uprawnień do wykonania tej operacji."}
                        },
                        "INVALID_CSRF": {
                            "summary": "CSRF token invalid",
                            "value": {"error_code": "INVALID_CSRF", "message": "CSRF token missing or invalid"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Category not found",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "CATEGORY_NOT_FOUND",
                        "message": "Category not found"
                    }
                }
            }
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "examples": {
                        "CREATE_FAILED": {
                            "summary": "Database error",
                            "value": {"error_code": "CREATE_FAILED", "message": "Failed to create the offer"}
                        },
                        "FILE_UPLOAD_FAILED": {
                            "summary": "File saving error",
                            "value": {"error_code": "FILE_UPLOAD_FAILED", "message": "Failed to upload the image"}
                        }
                    }
                }
            }
        }
    }
)
async def create_offer(
    background_tasks: BackgroundTasks,
    request: Request,
    title: str = Form(...),
    price: Decimal = Form(...),
    category_id: int = Form(...),
    quantity: int = Form(1),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    session_data: dict = Depends(require_seller),
    offer_service: OfferService = Depends(get_offer_service),
    media_service: MediaService = Depends(get_media_service),
    csrf_protect: CsrfProtect = Depends(),
):
    """
    Create a new product offer.
    
    This endpoint allows sellers to create new product listings with optional image upload.
    The offer will be created with an initial status of "inactive".
    
    ## Request
    - **title**: Product title (required)
    - **price**: Product price (required, must be greater than 0)
    - **category_id**: Category ID (required, must exist in the database)
    - **quantity**: Available quantity (default: 1, must be non-negative)
    - **description**: Product description (optional)
    - **image**: Product image file (optional, max 5MB, formats: JPG, PNG, WebP)
    
    ## Authentication
    - Requires user to be logged in
    - Requires Seller role
    - Requires valid CSRF token
    
    ## Response
    Returns the created offer details including:
    - Offer ID
    - Seller ID
    - Category ID
    - Title
    - Price
    - Image filename (if uploaded)
    - Quantity
    - Status (initially "inactive")
    - Creation timestamp
    
    ## Error Codes
    - INVALID_INPUT: Missing or invalid fields in request
    - INVALID_PRICE: Price must be greater than 0
    - INVALID_QUANTITY: Quantity cannot be negative
    - INVALID_FILE_TYPE: Unsupported image format
    - FILE_TOO_LARGE: Image exceeds size limit
    - NOT_AUTHENTICATED: User not logged in
    - INSUFFICIENT_PERMISSIONS: User is not a seller
    - INVALID_CSRF: Missing or invalid CSRF token
    - CATEGORY_NOT_FOUND: Specified category does not exist
    - CREATE_FAILED: Database error during offer creation
    - FILE_UPLOAD_FAILED: Error saving the image file
    
    ## Notes
    - All fields except image and description are required
    - New offers are created with "inactive" status by default
    - Seller can activate the offer later via a separate endpoint
    """
    try:
        # Verify CSRF token
        await csrf_protect.validate_csrf_in_cookies(request)
        
        # Get user ID from session data
        seller_id = session_data["user_id"]
        
        # Create the offer
        new_offer = await offer_service.create_offer(
            seller_id=seller_id,
            title=title,
            price=price,
            category_id=category_id,
            quantity=quantity,
            description=description,
            image=image,
            background_tasks=background_tasks
        )
        
        return new_offer
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating offer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "CREATE_FAILED",
                "message": "Failed to create the offer"
            }
        )

@router.post(
    "/{offer_id}/deactivate",
    response_model=OfferDetailDTO,
    responses={
        200: {"description": "Successfully deactivated the offer"},
        400: {
            "description": "Invalid status transition",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "INVALID_STATUS_TRANSITION",
                        "message": "Cannot deactivate offer with status 'sold'"
                    }
                }
            }
        },
        401: {
            "description": "User not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "NOT_AUTHENTICATED",
                        "message": "Użytkownik nie jest zalogowany."
                    }
                }
            }
        },
        403: {
            "description": "User not authorized",
            "content": {
                "application/json": {
                    "examples": {
                        "INSUFFICIENT_PERMISSIONS": {
                            "summary": "Not a seller",
                            "value": {"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Only sellers can deactivate offers"}
                        },
                        "NOT_OFFER_OWNER": {
                            "summary": "Not offer owner",
                            "value": {"error_code": "NOT_OFFER_OWNER", "message": "You can only deactivate your own offers"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Offer not found",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "OFFER_NOT_FOUND",
                        "message": "Offer not found"
                    }
                }
            }
        },
        409: {
            "description": "Offer already inactive",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "ALREADY_INACTIVE",
                        "message": "Offer is already inactive"
                    }
                }
            }
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "DEACTIVATION_FAILED",
                        "message": "Failed to deactivate offer"
                    }
                }
            }
        }
    }
)
async def deactivate_offer(
    offer_id: UUID = Path(
        ..., 
        description="UUID of the offer to deactivate",
        examples={"valid_uuid": {"value": "123e4567-e89b-12d3-a456-426614174000"}}
    ),
    current_user = Depends(require_seller),  # Require seller role
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger_dependency),
    csrf_protect: CsrfProtect = Depends(),
    request: Request = None,
):
    """
    Deactivate an offer by changing its status from 'active' to 'inactive'.
    
    - Requires Seller role and ownership of the offer
    - Offer must be in 'active' status
    - Returns the updated offer with seller and category information
    - CSRF protection is required for this endpoint
    """
    try:
        # Verify CSRF token
        await csrf_protect.validate_csrf_in_cookies(request)
        
        # Create service and call method
        offer_service = OfferService(db, logger)
        result = await offer_service.deactivate_offer(
            offer_id=offer_id,
            user_id=current_user.id,
            user_role=current_user.role
        )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (already handled in service)
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in deactivate_offer endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DEACTIVATION_FAILED",
                "message": "An unexpected error occurred"
            }
        ) 

@router.post(
    "/{offer_id}/mark-sold",
    response_model=OfferDetailDTO,
    responses={
        200: {"description": "Successfully marked the offer as sold"},
        400: {
            "description": "Invalid status transition",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "INVALID_STATUS_TRANSITION",
                        "message": "Cannot mark offer with status 'archived' as sold"
                    }
                }
            }
        },
        401: {
            "description": "User not authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "NOT_AUTHENTICATED",
                        "message": "Użytkownik nie jest zalogowany."
                    }
                }
            }
        },
        403: {
            "description": "User not authorized",
            "content": {
                "application/json": {
                    "examples": {
                        "INSUFFICIENT_PERMISSIONS": {
                            "summary": "Not a seller",
                            "value": {"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Only sellers can mark offers as sold"}
                        },
                        "NOT_OFFER_OWNER": {
                            "summary": "Not offer owner",
                            "value": {"error_code": "NOT_OFFER_OWNER", "message": "You can only mark your own offers as sold"}
                        },
                        "INVALID_CSRF": {
                            "summary": "CSRF token invalid",
                            "value": {"error_code": "INVALID_CSRF", "message": "CSRF token missing or invalid"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Offer not found",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "OFFER_NOT_FOUND",
                        "message": "Offer not found"
                    }
                }
            }
        },
        409: {
            "description": "Offer already sold",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "ALREADY_SOLD",
                        "message": "Offer is already marked as sold"
                    }
                }
            }
        },
        500: {
            "description": "Server error",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "MARK_SOLD_FAILED",
                        "message": "Failed to mark offer as sold"
                    }
                }
            }
        }
    }
)
async def mark_offer_as_sold(
    request: Request,
    offer_id: UUID = Path(
        ..., 
        description="UUID of the offer to mark as sold",
        examples={"valid_uuid": {"value": "123e4567-e89b-12d3-a456-426614174000"}}
    ),
    current_user = Depends(require_seller),
    offer_service: OfferService = Depends(get_offer_service),
    csrf_protect: CsrfProtect = Depends(),
):
    """
    Mark an offer as sold by changing its status to 'sold' and setting quantity to 0.
    
    - Requires Seller role and ownership of the offer
    - Offer must not be already sold, archived, or deleted
    - Operation is irreversible - once marked as sold, an offer cannot be activated again
    - Returns the updated offer with seller and category information
    - CSRF protection is required for this endpoint
    """
    try:
        # Verify CSRF token
        await csrf_protect.validate_csrf_in_cookies(request)
        
        # Create service and call method
        result = await offer_service.mark_offer_as_sold(
            offer_id=offer_id,
            user_id=current_user.id,
            user_role=current_user.role
        )
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (already handled in service)
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in mark_offer_as_sold endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "MARK_SOLD_FAILED", "message": "An unexpected error occurred"}
        ) 