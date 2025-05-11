from logging import Logger
from typing import Dict
from uuid import UUID

from fastapi import (APIRouter, Depends, HTTPException, Path, Query, Request,
                     status)
from fastapi_csrf_protect import CsrfProtect
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import (get_db_session, get_log_service, get_logger,
                          get_order_service, require_authenticated,
                          require_roles)
from exceptions.base import ConflictError
from models import UserModel
from schemas import (CreateOrderRequest, CreateOrderResponse, ErrorResponse,
                     LogEventType, OrderDetailDTO, OrderListResponse, UserRole)
from services.log_service import LogService
from services.order_service import OrderService

# Create router with "orders" prefix and tag
router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=CreateOrderResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Successfully created the order"},
        400: {"model": ErrorResponse, "description": "Invalid input data"},
        401: {"model": ErrorResponse, "description": "User not authenticated"},
        403: {"model": ErrorResponse, "description": "User not authorized"},
        404: {"model": ErrorResponse, "description": "Offer not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def create_order(
    request: Request,
    order_data: CreateOrderRequest,
    current_user: UserModel = Depends(require_roles([UserRole.BUYER])),
    order_service: OrderService = Depends(get_order_service),
    log_service: LogService = Depends(get_log_service),
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
    csrf_protect: CsrfProtect = Depends(),
):
    """
    Create a new order from cart items.

    This endpoint initiates the checkout process by:
    - Creating an order with the provided items
    - Setting the order status to 'pending_payment'
    - Creating a transaction record
    - Returning a payment URL for the mock payment system

    The endpoint requires:
    - User to be authenticated
    - User to have the Buyer role
    - Valid CSRF token in X-CSRF-Token header or cookie for protection against CSRF attacks

    ## Request
    - A list of items with offer_id and quantity

    ## Validation
    - Each offer must exist and be active
    - Each offer must have sufficient quantity

    ## Response
    - order_id: UUID of the created order
    - payment_url: URL to the payment gateway
    - status: Order status (pending_payment)
    - created_at: Timestamp when order was created
    """
    try:
        # Verify CSRF token
        try:
            csrf_protect.validate_csrf(request)
        except Exception as csrf_error:
            logger.error(f"CSRF validation failed: {str(csrf_error)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "INVALID_CSRF",
                    "message": "CSRF token missing or invalid",
                },
            )

        # Get client IP address for logging
        client_ip = request.client.host if request.client else None

        # Create order and get response using injected service
        result = await order_service.create_order(
            current_user=current_user,
            order_data=order_data,
            ip_address=client_ip,
        )

        # Return the result as CreateOrderResponse
        return CreateOrderResponse(**result)

    except HTTPException as e:
        # Re-raise known HTTP exceptions
        raise e
    except Exception as e:
        logger.error(
            f"Failed to create order for user {current_user['user_id'] if current_user else 'unknown'}: {e}",
            exc_info=True,
        )
        # Use injected log_service
        try:
            user_id_to_log = current_user["user_id"] if current_user else None
            await log_service.create_log(
                event_type=LogEventType.ORDER_PLACE_FAIL,
                user_id=user_id_to_log,
                message=f"Failed to create order: {str(e)}",
                ip_address=client_ip,
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order creation error: {log_error}",
                exc_info=True,
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "CREATE_ORDER_FAILED",
                "message": "Failed to create order",
            },
        )


@router.get(
    "",
    response_model=OrderListResponse,
    responses={
        200: {"description": "Successfully retrieved orders"},
        401: {"model": ErrorResponse, "description": "User not authenticated"},
        403: {"model": ErrorResponse, "description": "User not authorized"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def list_buyer_orders(
    request: Request,
    page: int = Query(1, ge=1, description="Page number to retrieve"),
    limit: int = Query(
        100, ge=1, le=100, description="Number of items per page (max 100)"
    ),
    current_user: Dict = Depends(require_roles([UserRole.BUYER])),
    order_service: OrderService = Depends(get_order_service),
    log_service: LogService = Depends(get_log_service),
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """
    Get a paginated list of the buyer's orders.

    This endpoint allows buyers to retrieve their order history with the following details for each order:
    - Order ID
    - Order status
    - Total amount
    - Creation date
    - Last update date (if any)

    The list is paginated and sorted by creation date (newest first).

    The endpoint requires:
    - User to be authenticated
    - User to have the Buyer role

    ## Query Parameters
    - page: Page number (default: 1, min: 1)
    - limit: Items per page (default: 100, min: 1, max: 100)

    ## Response
    Paginated list of orders with:
    - items: List of order summaries
    - total: Total number of orders
    - page: Current page number
    - limit: Number of items per page
    - pages: Total number of pages
    """
    try:
        # Access buyer ID using dictionary key
        buyer_id = current_user["user_id"]

        # Get orders using injected service
        result = await order_service.get_buyer_orders(
            buyer_id=buyer_id, page=page, limit=limit
        )

        return result

    except Exception as e:
        # Log the error
        logger.error(
            f"Error fetching orders for user {current_user['user_id']}: {str(e)}",
            exc_info=True,
        )

        # Log to database using injected service
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_LIST_FAIL,
                user_id=current_user["user_id"],
                message=f"Failed to fetch orders: {str(e)}",
                ip_address=request.client.host if request.client else None,
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order list error: {str(log_error)}",
                exc_info=True,
            )

        # Re-raise as HTTP exception if it's not already
        if not isinstance(e, HTTPException):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "FETCH_FAILED",
                    "message": "Failed to fetch orders",
                },
            )
        raise


@router.get(
    "/{order_id}",
    response_model=OrderDetailDTO,
    responses={
        200: {"description": "Successfully retrieved order details"},
        401: {"model": ErrorResponse, "description": "User not authenticated"},
        403: {"model": ErrorResponse, "description": "User not authorized"},
        404: {"model": ErrorResponse, "description": "Order not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def get_order_details(
    order_id: UUID = Path(..., description="UUID of the order to retrieve"),
    current_user: Dict = Depends(require_authenticated),
    order_service: OrderService = Depends(get_order_service),
    log_service: LogService = Depends(get_log_service),
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """
    Get detailed information about a specific order.

    This endpoint returns comprehensive details about an order, including:
    - Order ID, status, and timestamps
    - Buyer ID
    - List of all items in the order with quantities and prices
    - Total order amount

    Access controls are role-based:
    - Buyers can only view their own orders
    - Sellers can only view orders containing their products
    - Admins can view all orders

    ## Path Parameters
    - order_id: UUID of the order to retrieve

    ## Response
    Detailed order information including all order items and total amount
    """
    try:
        # Access user info using dictionary keys
        user_id = current_user["user_id"]
        user_role_str = current_user["user_role"]

        # Debug logging
        logger.info(
            f"Order details request - User ID: {user_id}, Role: {user_role_str}, Order ID: {order_id}"
        )

        # Convert user_role string to UserRole enum
        try:
            user_role = UserRole(user_role_str)
        except ValueError:
            # If conversion fails, log and use BUYER as fallback (safest default)
            logger.warning(
                f"Invalid user role: {user_role_str}, falling back to Buyer"
            )
            user_role = UserRole.BUYER

        # Convert UUID string to UUID if needed
        if isinstance(user_id, str):
            try:
                user_id = UUID(user_id)
            except ValueError:
                logger.error(f"Invalid user ID format: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "INVALID_USER_ID",
                        "message": "Invalid user ID format",
                    },
                )

        # Get order details using injected service
        result = await order_service.get_order_details(
            order_id=order_id, user_id=user_id, user_role=user_role
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        logger.error(
            f"Error fetching order details for order {order_id}, user {current_user['user_id']}: {str(e)}",
            exc_info=True,
        )

        # Log to database using injected service
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_DETAILS_FAIL,
                user_id=current_user["user_id"],
                message=f"Failed to fetch order details for order {order_id}: {str(e)}",
                ip_address="N/A",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order details error: {str(log_error)}",
                exc_info=True,
            )

        # Re-raise as HTTP exception if it's not already
        if not isinstance(e, HTTPException):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "FETCH_FAILED",
                    "message": "Failed to fetch order details",
                },
            )
        raise


@router.post(
    "/{order_id}/ship",
    summary="Ship an order",
    description="Mark an existing order as shipped. Seller must own at least one item in the order.",
    response_model=OrderDetailDTO,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Order shipped successfully"},
        400: {
            "model": ErrorResponse,
            "description": "Invalid order ID format",
        },
        401: {"model": ErrorResponse, "description": "User not authenticated"},
        403: {"model": ErrorResponse, "description": "User not authorized"},
        404: {"model": ErrorResponse, "description": "Order not found"},
        409: {"model": ErrorResponse, "description": "Invalid order status"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def ship_order(
    request: Request,
    order_id: UUID = Path(..., description="UUID of the order to ship"),
    user_data=Depends(require_roles([UserRole.SELLER])),
    order_service: OrderService = Depends(get_order_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger),
    csrf_protect: CsrfProtect = Depends(),
) -> OrderDetailDTO:
    """
    Mark an order as shipped. Seller must own at least one item in the order.
    """
    try:
        # Verify CSRF token
        try:
            csrf_protect.validate_csrf(request)
        except Exception as csrf_error:
            logger.error(
                f"CSRF validation failed for shipping order {order_id}: {str(csrf_error)}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "INVALID_CSRF",
                    "message": "CSRF token missing or invalid",
                },
            )

        seller_id = user_data["user_id"]
        updated_order = await order_service.ship_order(
            order_id=order_id, seller_id=seller_id
        )
        # Log success event
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_STATUS_CHANGE,
                user_id=seller_id,
                message=f"Order {order_id} shipped by seller {seller_id}",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order ship success: {log_error}", exc_info=True
            )

        return updated_order
    except ValueError as e:
        logger.warning(f"Order not found for shipping: {e}")
        # Log failure event
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_SHIP_FAIL,
                user_id=user_data["user_id"],
                message=f"Failed to ship order: {str(e)}",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order ship failure (ValueError): {log_error}",
                exc_info=True,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ORDER_NOT_FOUND", "message": str(e)},
        )
    except PermissionError as e:
        logger.warning(f"Permission denied for shipping order {order_id}: {e}")
        # Log failure event
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_SHIP_FAIL,
                user_id=user_data["user_id"],
                message=f"Failed to ship order: {str(e)}",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order ship failure (PermissionError): {log_error}",
                exc_info=True,
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": str(e),
            },
        )
    except ConflictError as e:
        logger.warning(f"Invalid status for shipping order {order_id}: {e}")
        # Log failure event
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_SHIP_FAIL,
                user_id=user_data["user_id"],
                message=f"Failed to ship order: {str(e)}",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order ship failure (ConflictError): {log_error}",
                exc_info=True,
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "INVALID_ORDER_STATUS", "message": str(e)},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error shipping order {order_id}: {e}", exc_info=True
        )
        # Log failure event
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_SHIP_FAIL,
                user_id=user_data["user_id"],
                message=f"Unexpected error shipping order {order_id}: {str(e)}",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order ship failure (Exception): {log_error}",
                exc_info=True,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "SHIP_FAILED",
                "message": "Failed to ship order",
            },
        )


@router.post(
    "/{order_id}/deliver",
    summary="Deliver an order",
    description="Mark an existing order as delivered. Seller must own at least one item in the order.",
    response_model=OrderDetailDTO,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Order delivered successfully"},
        400: {
            "model": ErrorResponse,
            "description": "Invalid order ID format",
        },
        401: {"model": ErrorResponse, "description": "User not authenticated"},
        403: {"model": ErrorResponse, "description": "User not authorized"},
        404: {"model": ErrorResponse, "description": "Order not found"},
        409: {"model": ErrorResponse, "description": "Invalid order status"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def deliver_order(
    request: Request,
    order_id: UUID = Path(..., description="UUID of the order to deliver"),
    user_data=Depends(require_roles([UserRole.SELLER])),
    order_service: OrderService = Depends(get_order_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger),
    csrf_protect: CsrfProtect = Depends(),
) -> OrderDetailDTO:
    """
    Mark an order as delivered. Seller must own at least one item in the order.
    """
    try:
        # Verify CSRF token
        try:
            csrf_protect.validate_csrf(request)
        except Exception as csrf_error:
            logger.error(
                f"CSRF validation failed for delivering order {order_id}: {str(csrf_error)}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "INVALID_CSRF",
                    "message": "CSRF token missing or invalid",
                },
            )

        seller_id = user_data["user_id"]
        updated_order = await order_service.deliver_order(
            order_id=order_id, seller_id=seller_id
        )
        # Log success event
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_STATUS_CHANGE,
                user_id=seller_id,
                message=f"Order {order_id} delivered by seller {seller_id}",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order deliver success: {log_error}",
                exc_info=True,
            )

        return updated_order
    except ValueError as e:
        logger.warning(f"Order not found for delivery: {e}")
        # Log failure event
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_DELIVER_FAIL,
                user_id=user_data["user_id"],
                message=f"Failed to deliver order: {str(e)}",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order deliver failure (ValueError): {log_error}",
                exc_info=True,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "ORDER_NOT_FOUND", "message": str(e)},
        )
    except PermissionError as e:
        logger.warning(
            f"Permission denied for delivering order {order_id}: {e}"
        )
        # Log failure event
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_DELIVER_FAIL,
                user_id=user_data["user_id"],
                message=f"Failed to deliver order: {str(e)}",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order deliver failure (PermissionError): {log_error}",
                exc_info=True,
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": str(e),
            },
        )
    except ConflictError as e:
        logger.warning(f"Invalid status for delivering order {order_id}: {e}")
        # Log failure event
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_DELIVER_FAIL,
                user_id=user_data["user_id"],
                message=f"Failed to deliver order: {str(e)}",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order deliver failure (ConflictError): {log_error}",
                exc_info=True,
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "INVALID_ORDER_STATUS", "message": str(e)},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error delivering order {order_id}: {e}", exc_info=True
        )
        # Log failure event
        try:
            await log_service.create_log(
                event_type=LogEventType.ORDER_DELIVER_FAIL,
                user_id=user_data["user_id"],
                message=f"Unexpected error delivering order {order_id}: {str(e)}",
            )
        except Exception as log_error:
            logger.error(
                f"Failed to log order deliver failure (Exception): {log_error}",
                exc_info=True,
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "DELIVER_FAILED",
                "message": "Failed to deliver order",
            },
        )
