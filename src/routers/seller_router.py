from fastapi import APIRouter, Depends, Request, Response, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from logging import Logger
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
from fastapi import HTTPException
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy import func

from dependencies import get_db_session, get_logger, require_seller, get_order_service, get_log_service
from schemas import UserRole, OrderListResponse, OfferSummaryDTO, PaginatedResponse, OfferStatus
from services.order_service import OrderService
from services.log_service import LogService
from models import LogEventType, OfferModel, CategoryModel, UserModel

router = APIRouter(prefix="/seller", tags=["seller"])

@router.get("/status", responses={
    200: {"description": "Seller account status information"},
    401: {"description": "User is not authenticated"},
    403: {"description": "User doesn't have seller privileges"}
})
async def get_seller_status(
    user_data: Dict = Depends(require_seller),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger)
):
    """
    Get seller account status.
    
    This endpoint provides information about the seller's account status.
    Only users with the Seller or Admin role can access this endpoint.
    
    Returns:
        Dict: Information about the seller's account
    """
    # This is just a demonstration endpoint
    # A real implementation would fetch seller-specific data from the database
    
    return {
        "seller_id": user_data["user_id"],
        "role": user_data["user_role"],
        "account_status": "active",
        "permissions": ["create_offer", "edit_offer", "manage_orders"],
        "metrics": {
            "total_offers": 0,
            "active_offers": 0,
            "sold_items": 0
        }
    }

@router.get("/offers/stats", responses={
    200: {"description": "Statistics about seller's offers"},
    401: {"description": "User is not authenticated"},
    403: {"description": "User doesn't have seller privileges"}
})
async def get_offer_stats(
    user_data: Dict = Depends(require_seller),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger)
):
    """
    Get statistics about seller's offers.
    
    This endpoint provides statistics about the seller's offers.
    Only users with the Seller or Admin role can access this endpoint.
    
    Returns:
        Dict: Statistics about the seller's offers
    """
    # This is just a demonstration endpoint
    # A real implementation would calculate statistics based on seller's offers
    
    return {
        "total_offers": 0,
        "offers_by_status": {
            "active": 0,
            "inactive": 0,
            "sold": 0,
            "moderated": 0,
            "archived": 0
        },
        "avg_price": 0,
        "total_sales": 0
    }

@router.get(
    "/account/sales",
    summary="List seller sales",
    description="Retrieve paginated list of orders containing products sold by the current seller.",
    response_model=OrderListResponse,
    responses={
        200: {
            "description": "Successfully retrieved sales history",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "uuid-order-id",
                                "status": "processing",
                                "total_amount": "123.45",
                                "created_at": "2024-01-01T12:00:00Z",
                                "updated_at": "2024-01-02T12:00:00Z"
                            }
                        ],
                        "total": 25,
                        "page": 1,
                        "limit": 100,
                        "pages": 1
                    }
                }
            }
        },
        401: {
            "description": "User not authenticated",
            "content": {
                "application/json": {
                    "example": {"error_code": "NOT_AUTHENTICATED", "message": "Użytkownik nie jest zalogowany."}
                }
            }
        },
        403: {
            "description": "User not authorized",
            "content": {
                "application/json": {
                    "example": {"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Nie masz uprawnień do wykonania tej operacji."}
                }
            }
        },
        500: {"description": "Server error", "content": {"application/json": {"example": {"error_code": "FETCH_FAILED", "message": "Failed to fetch sales data"}}}}
    }
)
async def list_seller_sales(
    user_data: Dict = Depends(require_seller),
    page: int = Query(1, ge=1, description="Page number to retrieve"),
    limit: int = Query(100, ge=1, le=100, description="Number of items per page (max 100)"),
    sort: str = Query("created_at_desc", description="Sort order (created_at_desc, created_at_asc, updated_at_desc, updated_at_asc, total_amount_desc, total_amount_asc, status_desc, status_asc)"),
    order_service: OrderService = Depends(get_order_service),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger)
):
    """
    Get a paginated list of orders containing products sold by the current seller.
    Only users with Seller or Admin roles can access this endpoint.
    """
    try:
        seller_id = user_data["user_id"]
        result = await order_service.get_seller_sales(
            seller_id=seller_id,
            page=page,
            limit=limit,
            sort=sort
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching seller sales: {str(e)}")
        log_service = LogService(db_session)
        await log_service.create_log(
            event_type=LogEventType.SALES_LIST_FAIL,
            user_id=user_data["user_id"],
            message=f"Failed to fetch sales data: {str(e)}",
            ip_address=None
        )
        await db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "FETCH_FAILED", "message": "Failed to fetch sales data"}
        )

@router.get(
    "/offers",
    summary="List seller's own offers",
    description="Retrieve paginated list of offers owned by the currently authenticated seller.",
    responses={
        200: {
            "description": "Successfully retrieved seller's offers",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "uuid-offer-id",
                                "seller_id": "uuid-seller-id",
                                "category_id": 1,
                                "title": "Sample Product",
                                "price": "99.99",
                                "image_filename": "image.png",
                                "quantity": 10,
                                "status": "active",
                                "created_at": "2023-01-01T00:00:00Z"
                            }
                        ],
                        "total": 25,
                        "page": 1,
                        "limit": 100,
                        "pages": 1
                    }
                }
            }
        },
        401: {
            "description": "User not authenticated",
            "content": {
                "application/json": {
                    "example": {"error_code": "NOT_AUTHENTICATED", "message": "Użytkownik nie jest zalogowany."}
                }
            }
        },
        403: {
            "description": "User not authorized",
            "content": {
                "application/json": {
                    "example": {"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Nie masz uprawnień do wykonania tej operacji."}
                }
            }
        },
        500: {"description": "Server error", "content": {"application/json": {"example": {"error_code": "FETCH_FAILED", "message": "Failed to fetch offers"}}}}
    }
)
async def list_seller_offers(
    user_data: Dict = Depends(require_seller),
    page: int = Query(1, ge=1, description="Page number to retrieve"),
    limit: int = Query(100, ge=1, le=100, description="Number of items per page (max 100)"),
    search: Optional[str] = Query(None, description="Search term for offer title and description"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    status: Optional[OfferStatus] = Query(None, description="Filter by offer status"),
    sort: Optional[str] = Query("created_at_desc", description="Sort order (price_asc, price_desc, created_at_desc)"),
    db_session: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger)
):
    """
    Get a paginated list of offers belonging to the current seller.
    Supports filtering, searching, and sorting.
    Only users with Seller role can access this endpoint.
    """
    try:
        seller_id = user_data["user_id"]
        
        # Start constructing a query
        query = select(OfferModel).filter(OfferModel.seller_id == seller_id)
        
        # Apply filters
        if category_id:
            query = query.filter(OfferModel.category_id == category_id)
        
        if status:
            query = query.filter(OfferModel.status == status)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (OfferModel.title.ilike(search_term)) | 
                (OfferModel.description.ilike(search_term))
            )
        
        # Apply sorting
        if sort == "price_asc":
            query = query.order_by(OfferModel.price.asc())
        elif sort == "price_desc":
            query = query.order_by(OfferModel.price.desc())
        else:  # Default to created_at_desc
            query = query.order_by(OfferModel.created_at.desc())
        
        # Count total results for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await db_session.execute(count_query)
        total_count = total_count_result.scalar() or 0
        
        # Apply pagination
        query = query.offset((page - 1) * limit).limit(limit)
        
        # Execute query
        result = await db_session.execute(query)
        offers = result.scalars().all()
        
        # Convert to DTOs
        offer_dtos = []
        for offer in offers:
            offer_dtos.append(
                OfferSummaryDTO(
                    id=str(offer.id),
                    seller_id=str(offer.seller_id),
                    category_id=offer.category_id,
                    title=offer.title,
                    price=str(offer.price),
                    image_filename=offer.image_filename,
                    quantity=offer.quantity,
                    status=offer.status,
                    created_at=offer.created_at
                )
            )
        
        # Calculate total pages
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        # Return paginated response
        return {
            "items": offer_dtos,
            "total": total_count,
            "page": page,
            "limit": limit,
            "pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Error fetching seller offers: {str(e)}")
        log_service = LogService(db_session)
        await log_service.create_log(
            event_type=LogEventType.OFFER_LIST_FAIL,
            user_id=user_data["user_id"],
            message=f"Failed to fetch seller offers: {str(e)}",
            ip_address=None
        )
        await db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "FETCH_FAILED", "message": "Failed to fetch offers"}
        ) 