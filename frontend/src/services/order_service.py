import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, func, join, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import PAYMENT_GATEWAY_URL
from models import (LogModel, OfferModel, OrderItemModel, OrderModel,
                    TransactionModel, UserModel)
from schemas import (CreateOrderRequest, LogEventType, OrderDetailDTO,
                     OrderItemDTO, OrderListResponse, OrderStatus,
                     OrderSummaryDTO, TransactionStatus, UserRole)


async def log_event(
    db_session: AsyncSession,
    event_type: LogEventType,
    user_id: UUID,
    message: str,
    ip_address: Optional[str] = None,
) -> None:
    """
    Helper function to log events to the database.

    Args:
        db_session: Database session
        event_type: Type of event from LogEventType enum
        user_id: UUID of the user
        message: Log message
        ip_address: Optional IP address
    """
    log = LogModel(
        event_type=event_type,
        user_id=user_id,
        ip_address=ip_address,
        message=message,
        timestamp=datetime.utcnow(),
    )

    db_session.add(log)
    # Don't commit here, let the caller handle transaction


class ConflictError(Exception):
    """Raised when there is a conflict with the current state of the resource."""


class OrderService:
    def __init__(self, db_session: AsyncSession, logger: logging.Logger):
        self.db_session = db_session
        self.logger = logger

    async def create_order(
        self,
        current_user: UserModel,
        order_data: CreateOrderRequest,
        ip_address: Optional[str] = None,
    ) -> Dict:
        """
        Create a new order with the given items.

        Args:
            current_user: The authenticated user making the order
            order_data: CreateOrderRequest with items to order
            ip_address: Optional IP address for logging

        Returns:
            Dictionary containing order_id, payment_url, status, and created_at

        Raises:
            HTTPException: If validation fails or order creation fails
        """
        # Log order creation start
        await log_event(
            self.db_session,
            LogEventType.ORDER_PLACE_START,
            current_user.id,
            f"Order creation started for user {current_user.email} with {len(order_data.items)} items",
            ip_address,
        )

        # Validate user role
        if current_user.role != UserRole.BUYER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "INSUFFICIENT_PERMISSIONS",
                    "message": "Only buyers can create orders",
                },
            )

        # Start transaction
        try:
            # Validate items - check if offers exist and are available
            offers_map = {}
            total_amount = Decimal("0.00")

            for item in order_data.items:
                offer = await self.db_session.get(OfferModel, item.offer_id)

                # Check if offer exists
                if not offer:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={
                            "error_code": "OFFER_NOT_FOUND",
                            "message": f"Offer with ID {item.offer_id} not found",
                        },
                    )

                # Check if offer is active
                if offer.status != "active":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error_code": "OFFER_NOT_AVAILABLE",
                            "message": f"Offer with ID {item.offer_id} is not active",
                        },
                    )

                # Check if quantity is sufficient
                if offer.quantity < item.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error_code": "INSUFFICIENT_QUANTITY",
                            "message": f"Insufficient quantity for offer {item.offer_id}. Available: {offer.quantity}, Requested: {item.quantity}",
                        },
                    )

                # Store offer in map for later use
                offers_map[str(item.offer_id)] = offer

                # Calculate item total and add to order total
                item_total = offer.price * Decimal(str(item.quantity))
                total_amount += item_total

            # Create order record
            order_id = uuid.uuid4()
            order = OrderModel(
                id=order_id,
                buyer_id=current_user.id,
                status=OrderStatus.PENDING_PAYMENT,
                created_at=datetime.utcnow(),
            )
            self.db_session.add(order)
            await self.db_session.flush()  # Flush to get the order ID

            # Create order items
            for item in order_data.items:
                offer = offers_map[str(item.offer_id)]
                order_item = OrderItemModel(
                    order_id=order_id,
                    offer_id=item.offer_id,
                    quantity=item.quantity,
                    price_at_purchase=offer.price,
                    offer_title=offer.title,
                )
                self.db_session.add(order_item)

            # Create transaction record
            transaction_id = uuid.uuid4()
            transaction = TransactionModel(
                id=transaction_id,
                order_id=order_id,
                status=TransactionStatus.FAIL,  # Default to fail until payment completes
                amount=total_amount,
                timestamp=datetime.utcnow(),
            )
            self.db_session.add(transaction)

            # Construct payment URL with transaction ID and callback URL
            callback_url = f"{PAYMENT_GATEWAY_URL}/payments/callback"
            payment_url = f"{PAYMENT_GATEWAY_URL}/pay?transaction_id={transaction_id}&amount={total_amount}&callback_url={callback_url}"

            # Commit the transaction
            await self.db_session.commit()

            # Log successful order creation
            await log_event(
                self.db_session,
                LogEventType.ORDER_PLACE_SUCCESS,
                current_user.id,
                f"Order {order_id} created successfully for user {current_user.email} with total amount {total_amount}",
                ip_address,
            )

            # Return the order details
            return {
                "order_id": order_id,
                "payment_url": payment_url,
                "status": OrderStatus.PENDING_PAYMENT,
                "created_at": order.created_at,
            }

        except HTTPException:
            # Rollback transaction and re-raise HTTP exceptions
            await self.db_session.rollback()
            raise

        except Exception as e:
            # Rollback transaction and handle unexpected errors
            await self.db_session.rollback()
            error_message = f"Error creating order: {str(e)}"
            self.logger.error(error_message)

            # Log order creation failure
            await log_event(
                self.db_session,
                LogEventType.ORDER_PLACE_FAIL,
                current_user.id,
                error_message,
                ip_address,
            )

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "ORDER_CREATION_FAILED",
                    "message": "An error occurred while processing your order",
                },
            )

    async def get_buyer_orders(
        self, buyer_id: UUID, page: int = 1, limit: int = 100
    ) -> OrderListResponse:
        """
        Get a paginated list of orders for a buyer.

        Args:
            buyer_id: UUID of the buyer
            page: Page number (starting from 1)
            limit: Number of items per page (max 100)

        Returns:
            OrderListResponse with paginated list of orders

        Raises:
            HTTPException: If there's an error fetching orders
        """
        try:
            # Validate page and limit
            if page < 1:
                page = 1
            if limit < 1:
                limit = 1
            if limit > 100:
                limit = 100

            # Calculate offset
            offset = (page - 1) * limit

            # Get total count of orders for this buyer
            count_query = (
                select(func.count())
                .select_from(OrderModel)
                .where(OrderModel.buyer_id == buyer_id)
            )
            total_count_result = await self.db_session.execute(count_query)
            total_count = total_count_result.scalar()

            # Calculate total pages
            total_pages = (
                (total_count + limit - 1) // limit if total_count > 0 else 1
            )

            # Build query to get orders with their total amount
            query = (
                select(
                    OrderModel,
                    func.sum(
                        OrderItemModel.price_at_purchase
                        * OrderItemModel.quantity
                    ).label("total_amount"),
                )
                .join(OrderItemModel, OrderItemModel.order_id == OrderModel.id)
                .where(OrderModel.buyer_id == buyer_id)
                .group_by(OrderModel.id)
                .order_by(OrderModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )

            # Execute query
            result = await self.db_session.execute(query)
            rows = result.all()

            # Transform to DTOs
            items = []
            for row in rows:
                order = row[0]  # OrderModel
                total_amount = row[1]  # total_amount

                items.append(
                    OrderSummaryDTO(
                        id=order.id,
                        status=order.status,
                        total_amount=total_amount,
                        created_at=order.created_at,
                        updated_at=order.updated_at,
                    )
                )

            # Return paginated response
            return OrderListResponse(
                items=items,
                total=total_count,
                page=page,
                limit=limit,
                pages=total_pages,
            )

        except Exception as e:
            self.logger.error(f"Error fetching buyer orders: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "FETCH_FAILED",
                    "message": "Failed to fetch orders",
                },
            )

    async def get_order_details(
        self, order_id: UUID, user_id: UUID, user_role: UserRole
    ) -> OrderDetailDTO:
        """
        Get detailed information about a specific order.

        Args:
            order_id: UUID of the order
            user_id: UUID of the user requesting the details
            user_role: Role of the user (BUYER, SELLER, ADMIN)

        Returns:
            OrderDetailDTO with detailed order information including items

        Raises:
            HTTPException: If order not found or user does not have permission
        """
        try:
            # First check if order exists
            order_query = select(OrderModel).where(OrderModel.id == order_id)
            order_result = await self.db_session.execute(order_query)
            order = order_result.scalar_one_or_none()

            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "error_code": "ORDER_NOT_FOUND",
                        "message": f"Order with ID {order_id} not found",
                    },
                )

            # Authorization check based on user role
            if user_role == UserRole.BUYER:
                # Buyer can only view their own orders
                if order.buyer_id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "error_code": "ACCESS_DENIED",
                            "message": "User does not have permission to view this order",
                        },
                    )
            elif user_role == UserRole.SELLER:
                # Seller can only view orders that contain their offers
                # Need to check if any of the order items belong to offers from this seller
                seller_check_query = (
                    select(func.count())
                    .select_from(
                        join(
                            OrderItemModel,
                            OfferModel,
                            OrderItemModel.offer_id == OfferModel.id,
                        )
                    )
                    .where(
                        and_(
                            OrderItemModel.order_id == order_id,
                            OfferModel.seller_id == user_id,
                        )
                    )
                )
                seller_check_result = await self.db_session.execute(
                    seller_check_query
                )
                seller_items_count = seller_check_result.scalar()

                if seller_items_count == 0:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail={
                            "error_code": "ACCESS_DENIED",
                            "message": "User does not have permission to view this order",
                        },
                    )
            # For ADMIN role, no additional permission check is needed

            # Fetch order items with their details
            items_query = select(OrderItemModel).where(
                OrderItemModel.order_id == order_id
            )
            items_result = await self.db_session.execute(items_query)
            order_items = items_result.scalars().all()

            # Calculate total amount
            total_amount = Decimal("0.00")
            items_dto = []

            for item in order_items:
                item_total = item.price_at_purchase * item.quantity
                total_amount += item_total

                items_dto.append(
                    OrderItemDTO(
                        id=item.id,
                        offer_id=item.offer_id,
                        quantity=item.quantity,
                        price_at_purchase=item.price_at_purchase,
                        offer_title=item.offer_title,
                    )
                )

            # Create and return the OrderDetailDTO
            return OrderDetailDTO(
                id=order.id,
                buyer_id=order.buyer_id,
                status=order.status,
                created_at=order.created_at,
                updated_at=order.updated_at,
                items=items_dto,
                total_amount=total_amount,
            )

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log unexpected errors
            self.logger.error(f"Error fetching order details: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "FETCH_FAILED",
                    "message": "Failed to fetch order details",
                },
            )

    async def get_seller_sales(
        self, seller_id: UUID, page: int = 1, limit: int = 100
    ) -> OrderListResponse:
        """
        Get a paginated list of orders containing offers from the specified seller.
        """
        try:
            # Validate page and limit
            if page < 1:
                page = 1
            if limit < 1:
                limit = 1
            if limit > 100:
                limit = 100

            offset = (page - 1) * limit

            # Total count of distinct orders for this seller
            count_query = (
                select(func.count(func.distinct(OrderModel.id)))
                .select_from(OrderModel)
                .join(OrderItemModel, OrderModel.id == OrderItemModel.order_id)
                .join(OfferModel, OrderItemModel.offer_id == OfferModel.id)
                .where(OfferModel.seller_id == seller_id)
            )
            count_result = await self.db_session.execute(count_query)
            total_count = count_result.scalar() or 0

            # Query orders with total amount
            query = (
                select(
                    OrderModel.id,
                    OrderModel.status,
                    OrderModel.created_at,
                    OrderModel.updated_at,
                    func.sum(
                        OrderItemModel.price_at_purchase
                        * OrderItemModel.quantity
                    ).label("total_amount"),
                )
                .select_from(OrderModel)
                .join(OrderItemModel, OrderModel.id == OrderItemModel.order_id)
                .join(OfferModel, OrderItemModel.offer_id == OfferModel.id)
                .where(OfferModel.seller_id == seller_id)
                .group_by(
                    OrderModel.id,
                    OrderModel.status,
                    OrderModel.created_at,
                    OrderModel.updated_at,
                )
                .order_by(OrderModel.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await self.db_session.execute(query)
            records = result.all()

            items = [
                OrderSummaryDTO(
                    id=rec[0],
                    status=rec[1],
                    total_amount=rec[4],
                    created_at=rec[2],
                    updated_at=rec[3],
                )
                for rec in records
            ]

            pages = (
                (total_count + limit - 1) // limit if total_count > 0 else 1
            )

            return OrderListResponse(
                items=items,
                total=total_count,
                page=page,
                limit=limit,
                pages=pages,
            )
        except Exception as e:
            self.logger.error(f"Error fetching seller sales: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error_code": "FETCH_FAILED",
                    "message": "Failed to fetch sales data",
                },
            )

    async def ship_order(
        self, order_id: UUID, seller_id: UUID
    ) -> OrderDetailDTO:
        """
        Ship an order by marking its status from 'processing' to 'shipped'.
        Raises:
            ValueError: if order not found
            PermissionError: if seller does not own any items in the order
            ConflictError: if order is not in 'processing' status
        """
        # Check if order exists
        order_query = select(OrderModel).where(OrderModel.id == order_id)
        order_result = await self.db_session.execute(order_query)
        order = order_result.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Check order status
        if order.status != OrderStatus.PROCESSING:
            raise ConflictError(
                "Order must be in 'processing' status to be shipped"
            )

        # Check seller ownership of at least one item
        seller_check_query = (
            select(func.count())
            .select_from(
                join(
                    OrderItemModel,
                    OfferModel,
                    OrderItemModel.offer_id == OfferModel.id,
                )
            )
            .where(
                and_(
                    OrderItemModel.order_id == order_id,
                    OfferModel.seller_id == seller_id,
                )
            )
        )
        seller_items_count = (
            await self.db_session.execute(seller_check_query)
        ).scalar() or 0
        if seller_items_count == 0:
            raise PermissionError(
                "Seller does not own any items in this order"
            )

        # Update order status and timestamp
        order.status = OrderStatus.SHIPPED
        order.updated_at = datetime.utcnow()
        self.db_session.add(order)
        await self.db_session.flush()

        # Return detailed order info
        return await self.get_order_details(
            order_id, seller_id, UserRole.SELLER
        )

    async def deliver_order(
        self, order_id: UUID, seller_id: UUID
    ) -> OrderDetailDTO:
        """
        Deliver an order by marking its status from 'shipped' to 'delivered'.
        Raises:
            ValueError: if order not found
            PermissionError: if seller does not own any items in the order
            ConflictError: if order is not in 'shipped' status
        """
        # Check if order exists
        order_query = select(OrderModel).where(OrderModel.id == order_id)
        order_result = await self.db_session.execute(order_query)
        order = order_result.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Check order status
        if order.status != OrderStatus.SHIPPED:
            raise ConflictError(
                "Order must be in 'shipped' status to be delivered"
            )

        # Check seller ownership of at least one item
        seller_check_query = (
            select(func.count())
            .select_from(
                join(
                    OrderItemModel,
                    OfferModel,
                    OrderItemModel.offer_id == OfferModel.id,
                )
            )
            .where(
                and_(
                    OrderItemModel.order_id == order_id,
                    OfferModel.seller_id == seller_id,
                )
            )
        )
        seller_items_count = (
            await self.db_session.execute(seller_check_query)
        ).scalar() or 0
        if seller_items_count == 0:
            raise PermissionError(
                "Seller does not own any items in this order"
            )

        # Update order status and timestamp
        order.status = OrderStatus.DELIVERED
        order.updated_at = datetime.utcnow()
        self.db_session.add(order)
        await self.db_session.flush()

        # Return detailed order info
        return await self.get_order_details(
            order_id, seller_id, UserRole.SELLER
        )

    async def get_admin_orders(
        self,
        page: int = 1,
        limit: int = 100,
        status: Optional[OrderStatus] = None,
        buyer_id: Optional[UUID] = None,
        seller_id: Optional[UUID] = None,
    ) -> Tuple[List[OrderSummaryDTO], int, int]:
        """
        Retrieve a paginated list of all orders for admin, with optional filters by status, buyer, and seller.
        """
        # Validate parameters
        if page < 1:
            raise ValueError("Page must be a positive integer")
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        # Build base query
        base_query = select(OrderModel)
        if status:
            base_query = base_query.where(OrderModel.status == status)
        if buyer_id:
            base_query = base_query.where(OrderModel.buyer_id == buyer_id)
        if seller_id:
            base_query = (
                base_query.join(OrderItemModel)
                .join(OfferModel, OrderItemModel.offer_id == OfferModel.id)
                .where(OfferModel.seller_id == seller_id)
            )

        # Count total orders for pagination
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db_session.execute(count_query)).scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * limit
        result = await self.db_session.execute(
            base_query.order_by(OrderModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        orders = result.scalars().all()

        # Calculate total pages
        pages = (total + limit - 1) // limit

        # Map to DTOs with total_amount calculation
        summaries: List[OrderSummaryDTO] = []
        for order in orders:
            # Fetch items for each order
            items_res = await self.db_session.execute(
                select(OrderItemModel).where(
                    OrderItemModel.order_id == order.id
                )
            )
            items = items_res.scalars().all()
            # Calculate total amount
            total_amount = sum(
                item.quantity * item.price_at_purchase for item in items
            )
            summaries.append(
                OrderSummaryDTO(
                    id=order.id,
                    status=order.status,
                    total_amount=total_amount,
                    created_at=order.created_at,
                    updated_at=order.updated_at,
                )
            )

        return summaries, total, pages

    async def cancel_order(self, order_id: UUID) -> OrderDetailDTO:
        """
        Cancel an order by changing its status to 'cancelled'.
        """
        # Retrieve the order
        order_query = select(OrderModel).where(OrderModel.id == order_id)
        result = await self.db_session.execute(order_query)
        order = result.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        # Ensure the order is not already cancelled or delivered
        if order.status == OrderStatus.CANCELLED:
            raise ValueError(f"Order {order_id} is already cancelled")
        if order.status == OrderStatus.DELIVERED:
            raise ValueError(
                f"Order {order_id} is already delivered and cannot be cancelled"
            )
        # Update status and timestamp
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()
        self.db_session.add(order)
        try:
            await self.db_session.commit()
        except Exception as e:
            await self.db_session.rollback()
            self.logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            raise Exception("Failed to cancel order")
        # Return the updated order details for admin
        return await self.get_order_details(
            order_id, order.buyer_id, UserRole.ADMIN
        )
