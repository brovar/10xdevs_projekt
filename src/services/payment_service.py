from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.sql import join, and_
import logging

from models import TransactionModel, OrderModel, OrderItemModel, OfferModel, LogModel
from schemas import TransactionStatus, OrderStatus
from schemas import LogEventType
from .order_service import ConflictError
from .log_service import LogService

class PaymentResult:
    """Result of processing a payment callback."""
    def __init__(self, order_status: OrderStatus):
        self.order_status = order_status

class PaymentService:
    """Service for handling payment callbacks and updating transactions, orders, and inventory."""
    def __init__(self, db_session: AsyncSession, logger: logging.Logger):
        self.db_session = db_session
        self.logger = logger

    async def process_payment_callback(
        self,
        transaction_id: UUID,
        status: TransactionStatus
    ) -> PaymentResult:
        """
        Process a payment callback:
        - Update transaction and order status
        - Adjust inventory on success
        Raises:
            ValueError: transaction or order not found
            ConflictError: order already processed
        """
        # Fetch transaction
        tx_query = select(TransactionModel).where(TransactionModel.id == transaction_id)
        tx_result = await self.db_session.execute(tx_query)
        transaction = tx_result.scalar_one_or_none()
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Fetch related order
        order_id = transaction.order_id
        order_query = select(OrderModel).where(OrderModel.id == order_id)
        order_result = await self.db_session.execute(order_query)
        order = order_result.scalar_one_or_none()
        if not order:
            raise ValueError(f"Order not found for transaction {transaction_id}")

        # Check for idempotency
        if order.status != OrderStatus.PENDING_PAYMENT:
            raise ConflictError(f"Order {order_id} has already been processed")

        # Determine new order status
        new_order_status = OrderStatus.PROCESSING
        if status == TransactionStatus.FAIL:
            new_order_status = OrderStatus.FAILED
        elif status == TransactionStatus.CANCELLED:
            new_order_status = OrderStatus.CANCELLED

        # Perform updates in a transaction
        try:
            # Update transaction status
            transaction.status = status
            self.db_session.add(transaction)

            # Update order status and timestamp
            order.status = new_order_status
            order.updated_at = datetime.utcnow()
            self.db_session.add(order)

            # On success, adjust inventory
            if status == TransactionStatus.SUCCESS:
                items_query = select(OrderItemModel).where(OrderItemModel.order_id == order_id)
                items_result = await self.db_session.execute(items_query)
                order_items = items_result.scalars().all()
                for item in order_items:
                    offer = await self.db_session.get(OfferModel, item.offer_id)
                    if offer:
                        offer.quantity = offer.quantity - item.quantity
                        # Mark sold if depleted
                        if offer.quantity == 0 and offer.status == 'active':
                            offer.status = 'sold'
                        self.db_session.add(offer)

            # Commit changes
            await self.db_session.commit()
        except Exception:
            await self.db_session.rollback()
            raise

        return PaymentResult(order_status=new_order_status) 