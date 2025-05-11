from fastapi import APIRouter, Depends, HTTPException, status, Request, Path
from fastapi_csrf_protect import CsrfProtect
from logging import Logger
from uuid import UUID

from dependencies import get_log_service, get_user_service, require_admin, get_logger, get_offer_service, get_order_service
from services.user_service import UserService
from services.log_service import LogService
from schemas import UserListResponse, UserListQueryParams, LogEventType, UserDTO, OfferListResponse, AdminOfferListQueryParams, OfferDetailDTO, OrderListResponse, AdminOrderListQueryParams, OrderDetailDTO, ErrorResponse, LogListResponse, AdminLogListQueryParams
from services.offer_service import OfferService
from services.order_service import OrderService

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all users (Admin)",
    description="Retrieves a paginated list of all users with filtering options. Requires Admin role.",
    responses={
        200: {"description": "Successful response with paginated user list"},
        400: {"model": ErrorResponse, "description": "Invalid query parameters"},
        401: {"model": ErrorResponse, "description": "User not authenticated"},
        403: {"model": ErrorResponse, "description": "User does not have Admin role"},
        500: {"model": ErrorResponse, "description": "Server error while fetching data"}
    }
)
async def list_users(
    query_params: UserListQueryParams = Depends(),
    current_user: UserDTO = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger)
):
    """Endpoint handler to list users with filtering and pagination, admin only."""
    try:
        # Log access attempt
        await log_service.create_log(
            event_type=LogEventType.ADMIN_LIST_USERS,
            user_id=current_user.id,
            message=f"Admin {current_user.email} accessed user list with params: {query_params.dict(exclude_none=True)}"
        )
        
        # Fetch users from service
        result = await user_service.list_users(
            page=query_params.page,
            limit=query_params.limit,
            role=query_params.role,
            status=query_params.status,
            search=query_params.search
        )
        return result
        
    except ValueError as e:
        # Handle potential validation errors from service (though Pydantic handles most)
        logger.warning(f"Invalid query parameter error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_QUERY_PARAM",
                "message": str(e)
            }
        )
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Failed to fetch users: {str(e)}", exc_info=True)
        await log_service.create_log(
            event_type=LogEventType.ADMIN_LIST_USERS_FAIL,
            user_id=current_user.id,
            message=f"Failed to fetch users: {str(e)}"
        )
        await log_service.db_session.commit() # Commit the log entry even if main transaction failed
        
        # Return standard server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "FETCH_FAILED",
                "message": "Failed to fetch users"
            }
        )

@router.get(
    "/users/{user_id}",
    response_model=UserDTO,
    summary="Get user details (Admin)",
    description="Retrieves details for a specific user. Requires Admin role.",
    responses={
        200: {"description": "User details retrieved successfully"},
        401: {"model": ErrorResponse, "description": "User not authenticated"},
        403: {"model": ErrorResponse, "description": "User does not have Admin role"},
        404: {"description": "User not found"},
        500: {"model": ErrorResponse, "description": "Server error while fetching data"}
    }
)
async def get_user_details(
    user_id: UUID = Path(..., description="The ID of the user to retrieve"),
    current_user: UserDTO = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger)
) -> UserDTO:
    """Retrieve detailed information for a specific user (admin only)."""
    try:
        # Log access attempt
        await log_service.create_log(
            event_type=LogEventType.ADMIN_GET_USER_DETAILS,
            user_id=current_user.id,
            message=f"Admin {current_user.email} accessed user details for user ID {user_id}"
        )
        # Fetch user details
        user = await user_service.get_user_by_id(user_id)
        if user is None:
            # Log failure
            await log_service.create_log(
                event_type=LogEventType.ADMIN_GET_USER_DETAILS_FAIL,
                user_id=current_user.id,
                message=f"User with ID {user_id} not found"
            )
            await log_service.db_session.commit()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error_code": "USER_NOT_FOUND", "message": "User not found"}
            )
        return user
    except ValueError as e:
        # Log unexpected error
        await log_service.create_log(
            event_type=LogEventType.ADMIN_GET_USER_DETAILS_FAIL,
            user_id=current_user.id,
            message=f"Failed to fetch user details: {str(e)}"
        )
        await log_service.db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "FETCH_FAILED", "message": "Failed to fetch user details"}
        )

@router.post(
    "/users/{user_id}/block",
    response_model=UserDTO,
    summary="Block user",
    description="Sets user status to 'Inactive'. If Seller, cancels active orders and sets offers to 'inactive'. Requires Admin role and valid CSRF token.",
    responses={
        200: {
            "description": "User blocked successfully",
            "content": {"application/json": {"example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "role": "Seller",
                "status": "Inactive",
                "first_name": "Jane",
                "last_name": "Doe",
                "created_at": "2023-09-01T12:34:56Z",
                "updated_at": "2023-09-02T10:00:00Z"
            }}}
        },
        401: {
            "description": "User not authenticated",
            "content": {"application/json": {"example": {"error_code": "NOT_AUTHENTICATED", "message": "Użytkownik nie jest zalogowany."}}}
        },
        403: {
            "description": "Forbidden: invalid CSRF token or insufficient permissions",
            "content": {"application/json": {"examples": {
                "INSUFFICIENT_PERMISSIONS": {"summary": "Admin role required", "value": {"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Admin role required"}},
                "INVALID_CSRF": {"summary": "Invalid CSRF token", "value": {"error_code": "INVALID_CSRF", "message": "CSRF token missing or invalid"}}
            }}}
        },
        404: {"description": "User not found", "content": {"application/json": {"example": {"error_code": "USER_NOT_FOUND", "message": "User not found"}}}},
        409: {"description": "User is already inactive", "content": {"application/json": {"example": {"error_code": "ALREADY_INACTIVE", "message": "User is already inactive"}}}},
        500: {"description": "Server error while blocking user", "content": {"application/json": {"example": {"error_code": "BLOCK_FAILED", "message": "Failed to block user"}}}}
    }
)
async def block_user(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
    user_id: UUID = Path(..., description="ID of user to block"),
    current_user: UserDTO = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger)
) -> UserDTO:
    """
    Block a user by setting their status to 'Inactive'. Requires Admin role.
    """
    # Verify CSRF token
    try:
        csrf_protect.validate_csrf(request)
    except Exception as csrf_error:
        logger.error(f"CSRF validation failed: {str(csrf_error)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INVALID_CSRF",
                "message": "CSRF token missing or invalid"
            }
        )
    
    # Log block attempt
    await log_service.create_log(
        event_type=LogEventType.USER_BLOCK_ATTEMPT,
        user_id=current_user.id,
        message=f"Admin {current_user.email} attempted to block user with ID {user_id}"
    )
    try:
        blocked_user = await user_service.block_user(user_id)
        # Log success
        await log_service.create_log(
            event_type=LogEventType.USER_DEACTIVATED,
            user_id=current_user.id,
            message=f"Admin {current_user.email} successfully blocked user {blocked_user.email} (ID: {user_id})"
        )
        return blocked_user
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            code, status_code = "USER_NOT_FOUND", status.HTTP_404_NOT_FOUND
        elif "already inactive" in msg.lower():
            code, status_code = "ALREADY_INACTIVE", status.HTTP_409_CONFLICT
        else:
            code, status_code = "INVALID_REQUEST", status.HTTP_400_BAD_REQUEST
        # Log failure
        await log_service.create_log(
            event_type=LogEventType.USER_BLOCK_FAIL,
            user_id=current_user.id,
            message=f"Failed to block user {user_id}: {msg}"
        )
        raise HTTPException(
            status_code=status_code,
            detail={"error_code": code, "message": msg}
        )
    except HTTPException:
        # Re-raise HTTP exceptions from service
        raise
    except Exception as e:
        # Log unexpected error
        await log_service.create_log(
            event_type=LogEventType.USER_BLOCK_FAIL,
            user_id=current_user.id,
            message=f"Unexpected error while blocking user {user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "BLOCK_FAILED", "message": "Failed to block user"}
        )

@router.post(
    "/users/{user_id}/unblock",
    response_model=UserDTO,
    summary="Unblock user",
    description="Sets user status to 'Active'. Requires Admin role and valid CSRF token.",
    responses={
        200: {
            "description": "User unblocked successfully",
            "content": {"application/json": {"example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "role": "Buyer",
                "status": "Active",
                "first_name": "John",
                "last_name": "Doe",
                "created_at": "2023-09-01T12:34:56Z",
                "updated_at": "2023-09-02T10:00:00Z"
            }}}
        },
        401: {
            "description": "User not authenticated",
            "content": {"application/json": {"example": {"error_code": "NOT_AUTHENTICATED", "message": "Użytkownik nie jest zalogowany."}}}
        },
        403: {
            "description": "Forbidden: invalid CSRF token or insufficient permissions",
            "content": {"application/json": {"examples": {
                "INSUFFICIENT_PERMISSIONS": {"summary": "Admin role required", "value": {"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Admin role required"}},
                "INVALID_CSRF": {"summary": "Invalid CSRF token", "value": {"error_code": "INVALID_CSRF", "message": "CSRF token missing or invalid"}}
            }}}
        },
        404: {"description": "User not found", "content": {"application/json": {"example": {"error_code": "USER_NOT_FOUND", "message": "User not found"}}}},
        409: {"description": "User is already active", "content": {"application/json": {"example": {"error_code": "ALREADY_ACTIVE", "message": "User is already active"}}}},
        500: {"description": "Server error while unblocking user", "content": {"application/json": {"example": {"error_code": "UNBLOCK_FAILED", "message": "Failed to unblock user"}}}}
    }
)
async def unblock_user(
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
    user_id: UUID = Path(..., description="ID of user to unblock"),
    current_user: UserDTO = Depends(require_admin),
    user_service: UserService = Depends(get_user_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger)
) -> UserDTO:
    """
    Unblock a user by setting their status to 'Active'. Requires Admin role.
    """
    # Verify CSRF token
    try:
        csrf_protect.validate_csrf(request)
    except Exception as csrf_error:
        logger.error(f"CSRF validation failed: {str(csrf_error)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INVALID_CSRF",
                "message": "CSRF token missing or invalid"
            }
        )
    
    # Log unblock attempt
    await log_service.create_log(
        event_type=LogEventType.USER_UNBLOCK_ATTEMPT,
        user_id=current_user.id,
        message=f"Admin {current_user.email} attempted to unblock user with ID {user_id}"
    )
    try:
        unblocked_user = await user_service.unblock_user(user_id)
        # Log success
        await log_service.create_log(
            event_type=LogEventType.USER_ACTIVATED,
            user_id=current_user.id,
            message=f"Admin {current_user.email} successfully unblocked user {unblocked_user.email} (ID: {user_id})"
        )
        return unblocked_user
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            code, status_code = "USER_NOT_FOUND", status.HTTP_404_NOT_FOUND
        elif "already active" in msg.lower():
            code, status_code = "ALREADY_ACTIVE", status.HTTP_409_CONFLICT
        else:
            code, status_code = "INVALID_REQUEST", status.HTTP_400_BAD_REQUEST
        # Log failure
        await log_service.create_log(
            event_type=LogEventType.USER_UNBLOCK_FAIL,
            user_id=current_user.id,
            message=f"Failed to unblock user {user_id}: {msg}"
        )
        raise HTTPException(
            status_code=status_code,
            detail={"error_code": code, "message": msg}
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected error
        await log_service.create_log(
            event_type=LogEventType.USER_UNBLOCK_FAIL,
            user_id=current_user.id,
            message=f"Unexpected error while unblocking user {user_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UNBLOCK_FAILED", "message": "Failed to unblock user"}
        )

# Admin: List all offers
@router.get(
    "/offers",
    response_model=OfferListResponse,
    summary="List all offers (Admin)",
    description="Retrieves a paginated list of all offers regardless of status. Requires Admin role.",
    responses={
        200: {"description": "Successful response with paginated offer list"},
        400: {"model": ErrorResponse, "description": "Invalid query parameters"},
        401: {"model": ErrorResponse, "description": "User not authenticated"},
        403: {"model": ErrorResponse, "description": "User does not have Admin role"},
        500: {"model": ErrorResponse, "description": "Server error while fetching data"}
    }
)
async def list_all_offers(
    query_params: AdminOfferListQueryParams = Depends(),
    current_user: UserDTO = Depends(require_admin),
    offer_service: OfferService = Depends(get_offer_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger)
) -> OfferListResponse:
    """
    Administrators can retrieve a paginated list of all offers, with advanced filtering, sorting, and pagination.
    """
    try:
        # Log access attempt
        await log_service.create_log(
            event_type=LogEventType.ADMIN_LIST_OFFERS,
            user_id=current_user.id,
            message=f"Admin {current_user.email} accessed offer list with params {query_params.dict(exclude_none=True)}"
        )
        # Fetch offers from service
        result = await offer_service.list_all_offers(
            search=query_params.search,
            category_id=query_params.category_id,
            seller_id=query_params.seller_id,
            status=query_params.status,
            sort=query_params.sort,
            page=query_params.page,
            limit=query_params.limit
        )
        return result
    except ValueError as e:
        # Handle invalid query parameters
        logger.warning(f"Invalid query parameter error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_QUERY_PARAM", "message": str(e)}
        )
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Failed to fetch offers: {e}", exc_info=True)
        await log_service.create_log(
            event_type=LogEventType.ADMIN_LIST_OFFERS_FAIL,
            user_id=current_user.id,
            message=f"Failed to fetch offers: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "FETCH_FAILED", "message": "Failed to fetch offers"}
        )

# Admin: Moderate an offer
@router.post(
    "/offers/{offer_id}/moderate",
    response_model=OfferDetailDTO,
    summary="Moderate offer",
    description="Sets offer status to 'moderated'. Requires Admin role.",
    responses={
        200: {"description": "Offer moderated successfully"},
        401: {"description": "User not authenticated"},
        403: {"description": "User does not have Admin role"},
        404: {"description": "Offer not found", "content": {"application/json": {"example": {"error_code": "OFFER_NOT_FOUND", "message": "Offer not found"}}}},
        409: {"description": "Offer is already moderated", "content": {"application/json": {"example": {"error_code": "ALREADY_MODERATED", "message": "Offer is already moderated"}}}},
        500: {"description": "Server error while moderating offer", "content": {"application/json": {"example": {"error_code": "MODERATION_FAILED", "message": "Failed to moderate offer"}}}}
    }
)
async def moderate_offer(
    offer_id: UUID = Path(..., description="The ID of the offer to moderate"),
    current_user: UserDTO = Depends(require_admin),
    offer_service: OfferService = Depends(get_offer_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger)
) -> OfferDetailDTO:
    """
    Moderates an offer by changing its status to 'moderated'. Requires Admin role.
    """
    # Log attempt
    await log_service.create_log(
        event_type=LogEventType.OFFER_MODERATION_ATTEMPT,
        user_id=current_user.id,
        message=f"Admin {current_user.email} attempted to moderate offer with ID {offer_id}"
    )
    try:
        moderated = await offer_service.moderate_offer(offer_id)
        # Log success
        await log_service.create_log(
            event_type=LogEventType.OFFER_MODERATED,
            user_id=current_user.id,
            message=f"Admin {current_user.email} successfully moderated offer with ID {offer_id}"
        )
        return moderated
    except HTTPException as e:
        # Log failure
        await log_service.create_log(
            event_type=LogEventType.OFFER_MODERATION_FAIL,
            user_id=current_user.id,
            message=f"Failed to moderate offer {offer_id}: {e.detail['message'] if isinstance(e.detail, dict) else str(e.detail)}"
        )
        raise
    except Exception as e:
        # Log unexpected error
        await log_service.create_log(
            event_type=LogEventType.OFFER_MODERATION_FAIL,
            user_id=current_user.id,
            message=f"Unexpected error while moderating offer {offer_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "MODERATION_FAILED", "message": "Failed to moderate offer"}
        )

# Admin: Unmoderate an offer
@router.post(
    "/offers/{offer_id}/unmoderate",
    response_model=OfferDetailDTO,
    summary="Unmoderate offer",
    description="Sets offer status from 'moderated' to 'inactive'. Requires Admin role.",
    responses={
        200: {"description": "Offer unmoderated successfully"},
        401: {"description": "User not authenticated"},
        403: {"description": "User does not have Admin role"},
        404: {"description": "Offer not found", "content": {"application/json": {"example": {"error_code": "OFFER_NOT_FOUND", "message": "Offer not found"}}}},
        409: {"description": "Offer is not moderated", "content": {"application/json": {"example": {"error_code": "NOT_MODERATED", "message": "Offer is not moderated"}}}},
        500: {"description": "Server error while unmoderating offer", "content": {"application/json": {"example": {"error_code": "UNMODERATION_FAILED", "message": "Failed to unmoderate offer"}}}}
    }
)
async def unmoderate_offer(
    offer_id: UUID = Path(..., description="The ID of the offer to unmoderate"),
    current_user: UserDTO = Depends(require_admin),
    offer_service: OfferService = Depends(get_offer_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger)
) -> OfferDetailDTO:
    """
    Unmoderates an offer by changing its status from 'moderated' to 'inactive'. Requires Admin role.
    """
    # Log attempt
    await log_service.create_log(
        event_type=LogEventType.OFFER_UNMODERATION_ATTEMPT,
        user_id=current_user.id,
        message=f"Admin {current_user.email} attempted to unmoderate offer with ID {offer_id}"
    )
    try:
        unmoderated = await offer_service.unmoderate_offer(offer_id)
        # Log success
        await log_service.create_log(
            event_type=LogEventType.OFFER_UNMODERATED,
            user_id=current_user.id,
            message=f"Admin {current_user.email} successfully unmoderated offer with ID {offer_id}"
        )
        return unmoderated
    except HTTPException as e:
        # Log failure
        await log_service.create_log(
            event_type=LogEventType.OFFER_UNMODERATION_FAIL,
            user_id=current_user.id,
            message=f"Failed to unmoderate offer {offer_id}: {e.detail['message'] if isinstance(e.detail, dict) else str(e.detail)}"
        )
        raise
    except Exception as e:
        # Log unexpected error
        await log_service.create_log(
            event_type=LogEventType.OFFER_UNMODERATION_FAIL,
            user_id=current_user.id,
            message=f"Unexpected error while unmoderating offer {offer_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UNMODERATION_FAILED", "message": "Failed to unmoderate offer"}
        )

# Admin: List all orders
@router.get(
    "/orders",
    response_model=OrderListResponse,
    summary="List all orders (Admin)",
    description="Retrieves a paginated list of all orders. Allows filtering by status, buyer_id, and seller_id. Requires Admin role.",
    responses={
        200: {"description": "Orders list retrieved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid query parameters"},
        401: {"model": ErrorResponse, "description": "User not authenticated"},
        403: {"model": ErrorResponse, "description": "User does not have Admin role"},
        500: {"model": ErrorResponse, "description": "Server error while fetching orders"}
    }
)
async def list_all_orders(
    query_params: AdminOrderListQueryParams = Depends(),
    current_user: UserDTO = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger)
) -> OrderListResponse:
    """
    Administrators can retrieve a paginated list of all orders, with optional filtering by status, buyer, and seller.
    """
    try:
        # Log access attempt
        filters = query_params.dict(exclude_none=True)
        await log_service.create_log(
            event_type=LogEventType.ADMIN_LIST_ORDERS,
            user_id=current_user.id,
            message=f"Admin {current_user.email} requested orders list with filters: {filters}, page={query_params.page}, limit={query_params.limit}"
        )
        # Fetch orders from service
        items, total, pages = await order_service.get_admin_orders(
            page=query_params.page,
            limit=query_params.limit,
            status=query_params.status,
            buyer_id=query_params.buyer_id,
            seller_id=query_params.seller_id
        )
        response = OrderListResponse(
            items=items,
            total=total,
            page=query_params.page,
            limit=query_params.limit,
            pages=pages
        )
        # Log success
        await log_service.create_log(
            event_type=LogEventType.ADMIN_LIST_ORDERS_SUCCESS,
            user_id=current_user.id,
            message=f"Successfully retrieved orders list. Total: {total}" 
        )
        return response

    except HTTPException:
        # Re-raise HTTP errors from service
        raise
    except ValueError as e:
        # Log validation failure
        await log_service.create_log(
            event_type=LogEventType.ADMIN_LIST_ORDERS_FAIL,
            user_id=current_user.id,
            message=f"Failed to retrieve orders list: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_QUERY_PARAM", "message": str(e)}
        )
    except Exception as e:
        # Log unexpected error
        await log_service.create_log(
            event_type=LogEventType.ADMIN_LIST_ORDERS_FAIL,
            user_id=current_user.id,
            message=f"Unexpected error while retrieving orders list: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "FETCH_FAILED", "message": "Failed to fetch orders"}
        )

# Admin: Cancel order
@router.post(
    "/orders/{order_id}/cancel",
    response_model=OrderDetailDTO,
    summary="Cancel order",
    description="Sets order status to 'cancelled'. Requires Admin role.",
    responses={
        200: {"description": "Order cancelled successfully"},
        400: {"model": ErrorResponse, "description": "Invalid query parameters"},
        401: {"model": ErrorResponse, "description": "User not authenticated"},
        403: {"model": ErrorResponse, "description": "User does not have Admin role"},
        404: {"model": ErrorResponse, "description": "Order not found", "content": {"application/json": {"example": {"error_code": "ORDER_NOT_FOUND", "message": "Order not found"}}}},
        409: {"model": ErrorResponse, "description": "Order cannot be cancelled", "content": {"application/json": {"example": {"error_code": "CANNOT_CANCEL", "message": "Order cannot be cancelled"}}}},
        500: {"model": ErrorResponse, "description": "Server error while cancelling order", "content": {"application/json": {"example": {"error_code": "CANCELLATION_FAILED", "message": "Failed to cancel order"}}}}
    }
)
async def cancel_order(
    order_id: UUID = Path(..., description="The ID of the order to cancel"),
    current_user: UserDTO = Depends(require_admin),
    order_service: OrderService = Depends(get_order_service),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger)
) -> OrderDetailDTO:
    """
    Cancel an order by changing its status to 'cancelled'. Only orders not yet delivered or cancelled.
    """
    # Log attempt
    await log_service.create_log(
        event_type=LogEventType.ORDER_CANCEL_ATTEMPT,
        user_id=current_user.id,
        message=f"Admin {current_user.email} attempted to cancel order with ID {order_id}"
    )
    try:
        cancelled = await order_service.cancel_order(order_id)
        # Log success
        await log_service.create_log(
            event_type=LogEventType.ORDER_CANCELLED,
            user_id=current_user.id,
            message=f"Admin {current_user.email} successfully cancelled order with ID {order_id}"
        )
        return cancelled
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            error_code = "ORDER_NOT_FOUND"
            status_code = status.HTTP_404_NOT_FOUND
        elif "already cancelled" in error_message.lower() or "cannot be cancelled" in error_message.lower():
            error_code = "CANNOT_CANCEL"
            status_code = status.HTTP_409_CONFLICT
        else:
            error_code = "INVALID_REQUEST"
            status_code = status.HTTP_400_BAD_REQUEST
        # Log failure
        await log_service.create_log(
            event_type=LogEventType.ORDER_CANCEL_FAIL,
            user_id=current_user.id,
            message=f"Failed to cancel order {order_id}: {error_message}"
        )
        raise HTTPException(
            status_code=status_code,
            detail={"error_code": error_code, "message": error_message}
        )
    except Exception as e:
        # Log unexpected error
        await log_service.create_log(
            event_type=LogEventType.ORDER_CANCEL_FAIL,
            user_id=current_user.id,
            message=f"Unexpected error while cancelling order {order_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "CANCELLATION_FAILED", "message": "Failed to cancel order"}
        )

# Admin: List logs
@router.get(
    "/logs",
    response_model=LogListResponse,
    summary="List logs (Admin)",
    description=(
        "Retrieves a paginated list of application logs. "
        "Supports filtering by event_type, user_id, ip_address, start_date, and end_date. "
        "Requires Admin role."
    ),
    responses={
        200: {
            "description": "Logs list retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 12345,
                                "event_type": "USER_LOGIN",
                                "user_id": "11111111-1111-1111-1111-111111111111",
                                "ip_address": "192.168.1.100",
                                "message": "Login successful for user@example.com",
                                "timestamp": "2023-04-15T12:00:00Z"
                            },
                            {
                                "id": 12344,
                                "event_type": "USER_REGISTER",
                                "user_id": "22222222-2222-2222-2222-222222222222",
                                "ip_address": "192.168.1.101",
                                "message": "New user registered: user2@example.com",
                                "timestamp": "2023-04-15T11:55:00Z"
                            }
                        ],
                        "total": 150,
                        "page": 1,
                        "limit": 100,
                        "pages": 2
                    }
                }
            }
        },
        400: {
            "model": ErrorResponse,
            "description": "Invalid query parameters",
            "content": {"application/json": {"example": {"error_code": "INVALID_QUERY_PARAM", "message": "Invalid query parameter: limit"}}}
        },
        401: {
            "model": ErrorResponse,
            "description": "User not authenticated",
            "content": {"application/json": {"example": {"error_code": "NOT_AUTHENTICATED", "message": "Authentication required"}}}
        },
        403: {
            "model": ErrorResponse,
            "description": "User does not have Admin role",
            "content": {"application/json": {"example": {"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Admin role required"}}}
        },
        500: {
            "model": ErrorResponse,
            "description": "Server error while fetching logs",
            "content": {"application/json": {"example": {"error_code": "FETCH_FAILED", "message": "Failed to fetch logs"}}}
        }
    }
)
async def list_logs(
    query_params: AdminLogListQueryParams = Depends(),
    current_user: UserDTO = Depends(require_admin),
    log_service: LogService = Depends(get_log_service),
    logger: Logger = Depends(get_logger)
) -> LogListResponse:
    """
    Retrieve a paginated list of application logs with optional filters (event_type, user_id, ip_address, date range).
    Access restricted to Admins.
    """
    try:
        # Log access attempt
        filters = query_params.dict(exclude_none=True)
        await log_service.create_log(
            event_type=LogEventType.ADMIN_ACTION,
            user_id=current_user.id,
            message=f"Admin {current_user.email} requested logs list with filters: {filters}, page={query_params.page}, limit={query_params.limit}"
        )
        # Fetch logs from service
        items, total, pages = await log_service.get_logs(
            page=query_params.page,
            limit=query_params.limit,
            event_type=query_params.event_type,
            user_id=query_params.user_id,
            ip_address=query_params.ip_address,
            start_date=query_params.start_date,
            end_date=query_params.end_date
        )
        response = LogListResponse(
            items=items,
            total=total,
            page=query_params.page,
            limit=query_params.limit,
            pages=pages
        )
        return response
    except ValueError as e:
        error_message = str(e)
        # Log validation failure
        await log_service.create_log(
            event_type=LogEventType.ADMIN_ACTION_FAIL,
            user_id=current_user.id,
            message=f"Failed to retrieve logs list: {error_message}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_QUERY_PARAM", "message": error_message}
        )
    except Exception as e:
        # Log unexpected error
        await log_service.create_log(
            event_type=LogEventType.ADMIN_ACTION_FAIL,
            user_id=current_user.id,
            message=f"Unexpected error while retrieving logs list: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "FETCH_FAILED", "message": "Failed to fetch logs"}
        ) 