from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db_session, get_logger, get_payment_service, get_log_service
from services.payment_service import PaymentService
from services.order_service import ConflictError
from schemas import PaymentCallbackResponse, TransactionStatus, LogEventType
from services.log_service import LogService

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get(
    "/callback",
    summary="Handle payment callback",
    description="Process transaction result notifications from the external payment provider. This endpoint is idempotent: repeated calls for the same transaction will not reprocess already-processed payments.",
    response_model=PaymentCallbackResponse,
    responses={
        200: {
            "description": "Callback processed successfully",
            "content": {"application/json": {"example": {"message": "Callback processed", "order_status": "processing"}}}
        },
        400: {
            "description": "Invalid or missing parameters",
            "content": {
                "application/json": {
                    "examples": {
                        "MISSING_PARAM": {
                            "summary": "Missing required parameter",
                            "value": {"error_code": "MISSING_PARAM", "message": "Missing required parameter: transaction_id"}
                        },
                        "INVALID_STATUS": {
                            "summary": "Invalid status value",
                            "value": {"error_code": "INVALID_STATUS", "message": "Invalid status value. Allowed values: success, fail, cancelled"}
                        }
                    }
                }
            }
        },
        404: {
            "description": "Transaction or order not found",
            "content": {
                "application/json": {
                    "examples": {
                        "TRANSACTION_NOT_FOUND": {
                            "summary": "Transaction not found",
                            "value": {"error_code": "TRANSACTION_NOT_FOUND", "message": "Transaction 123e4567-e89b-12d3-a456-426614174000 not found"}
                        },
                        "ORDER_NOT_FOUND": {
                            "summary": "Order not found for transaction",
                            "value": {"error_code": "ORDER_NOT_FOUND", "message": "Order not found for transaction 123e4567-e89b-12d3-a456-426614174000"}
                        }
                    }
                }
            }
        },
        409: {"description": "Order already processed", "content": {"application/json": {"example": {"error_code": "ORDER_ALREADY_PROCESSED", "message": "Order has already been processed"}}}},
        500: {"description": "Server error", "content": {"application/json": {"example": {"error_code": "CALLBACK_PROCESSING_FAILED", "message": "Failed to process payment callback"}}}}
    }
)
async def handle_payment_callback(
    transaction_id: Optional[UUID] = Query(None, description="Transaction ID"),
    status_str: Optional[str] = Query(None, description="Transaction status: success, fail, or cancelled"),
    payment_service: PaymentService = Depends(get_payment_service),
    log_service = Depends(get_log_service),
    logger: logging.Logger = Depends(get_logger)
) -> PaymentCallbackResponse:
    # Validate presence of required parameters
    if transaction_id is None:
        await log_service.create_log(
            event_type=LogEventType.PAYMENT_CALLBACK_FAIL,
            message=f"Missing required parameter: transaction_id"
        )
        await log_service.db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "MISSING_PARAM", "message": "Missing required parameter: transaction_id"}
        )
    if status_str is None:
        await log_service.create_log(
            event_type=LogEventType.PAYMENT_CALLBACK_FAIL,
            message=f"Missing required parameter: status"
        )
        await log_service.db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "MISSING_PARAM", "message": "Missing required parameter: status"}
        )
    # Validate status parameter
    try:
        transaction_status = TransactionStatus(status_str)
    except ValueError:
        await log_service.create_log(
            event_type=LogEventType.PAYMENT_CALLBACK_FAIL,
            message=f"Invalid payment status: {status_str} for transaction {transaction_id}"
        )
        await log_service.db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_STATUS", "message": "Invalid status value. Allowed values: success, fail, cancelled"}
        )

    try:
        # Process callback
        result = await payment_service.process_payment_callback(
            transaction_id=transaction_id,
            status=transaction_status
        )
        # Log success
        await log_service.create_log(
            event_type=LogEventType.PAYMENT_CALLBACK_SUCCESS,
            message=f"Successfully processed payment callback for transaction {transaction_id} with status {status_str}"
        )
        return PaymentCallbackResponse(
            message="Callback processed",
            order_status=result.order_status
        )
    except ValueError as e:
        error_message = str(e)
        error_code = "TRANSACTION_NOT_FOUND"
        status_code = status.HTTP_404_NOT_FOUND
        if "Order not found" in error_message:
            error_code = "ORDER_NOT_FOUND"
        await log_service.create_log(
            event_type=LogEventType.PAYMENT_CALLBACK_FAIL,
            message=f"Payment callback failed: {error_message}"
        )
        await log_service.db_session.commit()
        raise HTTPException(
            status_code=status_code,
            detail={"error_code": error_code, "message": error_message}
        )
    except ConflictError as e:
        error_message = str(e)
        await log_service.create_log(
            event_type=LogEventType.PAYMENT_CALLBACK_FAIL,
            message=f"Payment callback conflict: {error_message}"
        )
        await log_service.db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "ORDER_ALREADY_PROCESSED", "message": error_message}
        )
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing payment callback: {error_message}")
        await log_service.create_log(
            event_type=LogEventType.PAYMENT_CALLBACK_FAIL,
            message=f"Unexpected error processing payment callback: {error_message}"
        )
        await log_service.db_session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "CALLBACK_PROCESSING_FAILED", "message": "Failed to process payment callback"}
        ) 