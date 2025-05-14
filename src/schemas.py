import re
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# Enum Types from DB
class UserRole(str, Enum):
    BUYER = "Buyer"
    SELLER = "Seller"
    ADMIN = "Admin"


class UserStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DELETED = "Deleted"


class OfferStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD = "sold"
    MODERATED = "moderated"
    ARCHIVED = "archived"
    DELETED = "deleted"


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "pending_payment"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TransactionStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    CANCELLED = "cancelled"


class LogEventType(str, Enum):
    USER_LOGIN = "USER_LOGIN"
    USER_REGISTER = "USER_REGISTER"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    USER_PROFILE_UPDATE = "USER_PROFILE_UPDATE"
    CATEGORY_LIST_VIEWED = "CATEGORY_LIST_VIEWED"
    OFFER_CREATE = "OFFER_CREATE"
    OFFER_EDIT = "OFFER_EDIT"
    OFFER_STATUS_CHANGE = "OFFER_STATUS_CHANGE"
    ORDER_PLACE_START = "ORDER_PLACE_START"
    ORDER_PLACE_SUCCESS = "ORDER_PLACE_SUCCESS"
    ORDER_PLACE_FAIL = "ORDER_PLACE_FAIL"
    ORDER_LIST_FAIL = "ORDER_LIST_FAIL"
    ORDER_DETAILS_FAIL = "ORDER_DETAILS_FAIL"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_FAIL = "PAYMENT_FAIL"
    OFFER_MODERATED = "OFFER_MODERATED"
    OFFER_MODERATION_ATTEMPT = "OFFER_MODERATION_ATTEMPT"
    OFFER_MODERATION_FAIL = "OFFER_MODERATION_FAIL"
    USER_ACTIVATED = "USER_ACTIVATED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    USER_BLOCK_ATTEMPT = "USER_BLOCK_ATTEMPT"
    USER_BLOCK_FAIL = "USER_BLOCK_FAIL"
    USER_DELETED = "USER_DELETED"
    USER_UNBLOCK_ATTEMPT = "USER_UNBLOCK_ATTEMPT"
    USER_UNBLOCK_FAIL = "USER_UNBLOCK_FAIL"
    SALES_LIST_FAIL = "SALES_LIST_FAIL"
    ORDER_STATUS_CHANGE = "ORDER_STATUS_CHANGE"
    ORDER_SHIP_FAIL = "ORDER_SHIP_FAIL"
    ORDER_DELIVER_FAIL = "ORDER_DELIVER_FAIL"
    PAYMENT_CALLBACK_SUCCESS = "PAYMENT_CALLBACK_SUCCESS"
    PAYMENT_CALLBACK_FAIL = "PAYMENT_CALLBACK_FAIL"
    ADMIN_LIST_USERS = "ADMIN_LIST_USERS"
    ADMIN_LIST_USERS_FAIL = "ADMIN_LIST_USERS_FAIL"
    ADMIN_GET_USER_DETAILS = "ADMIN_GET_USER_DETAILS"
    ADMIN_GET_USER_DETAILS_FAIL = "ADMIN_GET_USER_DETAILS_FAIL"
    ADMIN_LIST_OFFERS = "ADMIN_LIST_OFFERS"
    ADMIN_LIST_OFFERS_FAIL = "ADMIN_LIST_OFFERS_FAIL"
    OFFER_UNMODERATION_ATTEMPT = "OFFER_UNMODERATION_ATTEMPT"
    OFFER_UNMODERATED = "OFFER_UNMODERATED"
    OFFER_UNMODERATION_FAIL = "OFFER_UNMODERATION_FAIL"
    ADMIN_LIST_ORDERS = "ADMIN_LIST_ORDERS"
    ADMIN_LIST_ORDERS_SUCCESS = "ADMIN_LIST_ORDERS_SUCCESS"
    ADMIN_LIST_ORDERS_FAIL = "ADMIN_LIST_ORDERS_FAIL"
    ORDER_CANCEL_ATTEMPT = "ORDER_CANCEL_ATTEMPT"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    ORDER_CANCEL_FAIL = "ORDER_CANCEL_FAIL"
    ADMIN_ACTION = "ADMIN_ACTION"
    ADMIN_ACTION_FAIL = "ADMIN_ACTION_FAIL"


# Base Models
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    limit: int
    pages: int


# Auth DTOs
class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = Field(
        ..., description="User role, can be Buyer or Seller"
    )

    @field_validator("password")
    def password_strength(cls, v):
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r'[0-9!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError(
                "Password must contain a digit or special character"
            )
        return v

    @field_validator("role")
    def role_must_be_buyer_or_seller(cls, v):
        if v not in [UserRole.BUYER, UserRole.SELLER]:
            raise ValueError("Role must be Buyer or Seller for registration")
        return v


class UserBase(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole
    status: UserStatus
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime


class RegisterUserResponse(UserBase):
    pass


class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    def password_not_empty(cls, v):
        if not v:
            raise ValueError("Password cannot be empty")
        return v


class MessageResponse(BaseModel):
    message: str


class LoginUserResponse(MessageResponse):
    pass


class LogoutUserResponse(MessageResponse):
    pass


# User DTOs
class UserDTO(UserBase):
    updated_at: Optional[datetime] = None


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @field_validator("first_name")
    def validate_first_name(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError("First name cannot exceed 100 characters")
        return v

    @field_validator("last_name")
    def validate_last_name(cls, v):
        if v is not None and len(v) > 100:
            raise ValueError("Last name cannot exceed 100 characters")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    def password_strength(cls, v):
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain a lowercase letter")
        if not re.search(r'[0-9!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError(
                "Password must contain a digit or special character"
            )
        return v


class ChangePasswordResponse(MessageResponse):
    pass


# Category DTOs
class CategoryDTO(BaseModel):
    id: int
    name: str


class CategoriesListResponse(BaseModel):
    items: List[CategoryDTO]


# Offer DTOs
class OfferSummaryDTO(BaseModel):
    id: UUID
    seller_id: UUID
    category_id: int
    title: str
    price: Decimal
    image_filename: Optional[str] = None
    quantity: int
    status: OfferStatus
    created_at: datetime


class OfferListResponse(PaginatedResponse):
    items: List[OfferSummaryDTO]


class SellerInfoDTO(BaseModel):
    id: UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class OfferDetailDTO(OfferSummaryDTO):
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
    seller: SellerInfoDTO
    category: CategoryDTO

    class Config:
        json_schema_extra = {
            "examples": {
                "moderation_success": {
                    "summary": "Offer moderated successfully",
                    "value": {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "seller_id": "22222222-2222-2222-2222-222222222222",
                        "category_id": 1,
                        "title": "Sample Product",
                        "description": "Detailed description here.",
                        "price": "99.99",
                        "image_filename": "image.png",
                        "quantity": 10,
                        "status": "moderated",
                        "created_at": "2023-09-01T12:34:56Z",
                        "updated_at": "2023-09-02T10:00:00Z",
                        "seller": {
                            "id": "22222222-2222-2222-2222-222222222222",
                            "first_name": "SellerFirstName",
                            "last_name": "SellerLastName",
                        },
                        "category": {"id": 1, "name": "Electronics"},
                    },
                },
                "unmoderation_success": {
                    "summary": "Offer unmoderated successfully",
                    "value": {
                        "id": "33333333-3333-3333-3333-333333333333",
                        "seller_id": "44444444-4444-4444-4444-444444444444",
                        "category_id": 2,
                        "title": "Another Product",
                        "description": "Another description.",
                        "price": "49.99",
                        "image_filename": "another.png",
                        "quantity": 5,
                        "status": "inactive",
                        "created_at": "2023-09-03T08:00:00Z",
                        "updated_at": "2023-09-04T09:00:00Z",
                        "seller": {
                            "id": "44444444-4444-4444-4444-444444444444",
                            "first_name": "AnotherFirstName",
                            "last_name": "AnotherLastName",
                        },
                        "category": {"id": 2, "name": "Accessories"},
                    },
                },
            }
        }


class CreateOfferRequest(BaseModel):
    title: str
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    quantity: int = Field(1, ge=0)
    category_id: int

    @field_validator("price")
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v


class UpdateOfferRequest(CreateOfferRequest):
    pass


# Order DTOs
class OrderItemRequest(BaseModel):
    offer_id: UUID
    quantity: int = Field(..., gt=0)


class CreateOrderRequest(BaseModel):
    items: List[OrderItemRequest]

    @field_validator("items")
    def validate_items(cls, v):
        if not v:
            raise ValueError("Order must contain at least one item")
        return v


class CreateOrderResponse(BaseModel):
    order_id: UUID
    payment_url: str
    status: OrderStatus
    created_at: datetime


class OrderSummaryDTO(BaseModel):
    id: UUID
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime] = None


class OrderListResponse(PaginatedResponse):
    items: List[OrderSummaryDTO]


class OrderItemDTO(BaseModel):
    id: int
    offer_id: UUID
    quantity: int
    price_at_purchase: Decimal
    offer_title: str


class OrderDetailDTO(BaseModel):
    id: UUID
    buyer_id: UUID
    status: OrderStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[OrderItemDTO]
    total_amount: Decimal

    class Config:
        json_schema_extra = {
            "examples": {
                "cancel_success": {
                    "summary": "Order cancelled successfully",
                    "value": {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "buyer_id": "22222222-2222-2222-2222-222222222222",
                        "status": "cancelled",
                        "created_at": "2023-09-05T08:00:00Z",
                        "updated_at": "2023-09-05T09:00:00Z",
                        "items": [
                            {
                                "id": 1,
                                "offer_id": "33333333-3333-3333-3333-333333333333",
                                "quantity": 1,
                                "price_at_purchase": "50.00",
                                "offer_title": "Product Title 1",
                            },
                            {
                                "id": 2,
                                "offer_id": "44444444-4444-4444-4444-444444444444",
                                "quantity": 2,
                                "price_at_purchase": "36.73",
                                "offer_title": "Product Title 2",
                            },
                        ],
                        "total_amount": "123.45",
                    },
                }
            }
        }


# Payment DTOs
class PaymentCallbackResponse(BaseModel):
    message: str = Field(
        ..., description="A message indicating the callback processing result"
    )
    order_status: OrderStatus = Field(
        ...,
        description="The updated status of the order after processing the payment callback",
    )


# Admin DTOs
class UserListResponse(PaginatedResponse):
    items: List[UserDTO]


class LogDTO(BaseModel):
    id: int
    event_type: LogEventType
    user_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    message: str
    timestamp: datetime


class LogListResponse(PaginatedResponse):
    items: List[LogDTO]

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "id": 12345,
                        "event_type": "USER_LOGIN",
                        "user_id": "11111111-1111-1111-1111-111111111111",
                        "ip_address": "192.168.1.100",
                        "message": "Login successful for user@example.com",
                        "timestamp": "2023-04-15T12:00:00Z",
                    },
                    {
                        "id": 12344,
                        "event_type": "USER_REGISTER",
                        "user_id": "22222222-2222-2222-2222-222222222222",
                        "ip_address": "192.168.1.101",
                        "message": "New user registered: user2@example.com",
                        "timestamp": "2023-04-15T11:55:00Z",
                    },
                ],
                "total": 150,
                "page": 1,
                "limit": 100,
                "pages": 2,
            }
        }


# Admin Query Params
class UserListQueryParams(BaseModel):
    page: int = Field(1, gt=0, description="Page number")
    limit: int = Field(
        100, gt=0, le=100, description="Items per page"
    )
    role: Optional[UserRole] = Field(None, description="Filter by user role")
    status: Optional[UserStatus] = Field(
        None, description="Filter by user status"
    )
    search: Optional[str] = Field(
        None, description="Search by email, first name, or last name"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "limit": 50,
                "role": "Buyer",
                "status": "Active",
                "search": "john",
            }
        }


class AdminOfferListQueryParams(BaseModel):
    search: Optional[str] = Field(
        None, description="Search by title or description"
    )
    category_id: Optional[int] = Field(
        None, description="Filter by category ID"
    )
    seller_id: Optional[UUID] = Field(None, description="Filter by seller ID")
    status: Optional[OfferStatus] = Field(
        None, description="Filter by offer status"
    )
    sort: str = Field(
        "created_at_desc",
        description="Sorting criteria (price_asc, price_desc, created_at_desc, relevance)",
    )
    page: int = Field(1, gt=0, description="Page number")
    limit: int = Field(100, gt=0, le=100, description="Items per page")

    @field_validator("sort")
    def validate_sort(cls, v):
        allowed = ["price_asc", "price_desc", "created_at_desc", "relevance"]
        if v not in allowed:
            raise ValueError(f"Sort must be one of: {', '.join(allowed)}")
        return v

    class Config:
        json_schema_extra = {
            "examples": {
                "basic": {
                    "summary": "Basic pagination without filters",
                    "value": {
                        "page": 1,
                        "limit": 50,
                        "sort": "created_at_desc",
                    },
                },
                "search_and_filter": {
                    "summary": "Search by keywords and filter by category and status",
                    "value": {
                        "search": "headphones",
                        "category_id": 2,
                        "status": "inactive",
                        "sort": "price_desc",
                        "page": 2,
                        "limit": 20,
                    },
                },
            }
        }


class AdminOrderListQueryParams(BaseModel):
    page: int = Field(1, gt=0, description="Page number")
    limit: int = Field(
        100, gt=0, le=100, description="Items per page, max 100"
    )
    status: Optional[OrderStatus] = Field(
        None, description="Filter by order status"
    )
    buyer_id: Optional[UUID] = Field(None, description="Filter by buyer ID")
    seller_id: Optional[UUID] = Field(
        None,
        description="Filter by seller ID (orders containing items from this seller)",
    )

    class Config:
        json_schema_extra = {
            "examples": {
                "basic": {
                    "summary": "Basic pagination without filters",
                    "value": {"page": 1, "limit": 100},
                },
                "with_filters": {
                    "summary": "Filter by status and buyer",
                    "value": {
                        "status": "shipped",
                        "buyer_id": "11111111-1111-1111-1111-111111111111",
                        "limit": 50,
                    },
                },
            }
        }


class AdminLogListQueryParams(BaseModel):
    page: int = Field(1, gt=0, description="Page number, starting from 1")
    limit: int = Field(
        100, gt=0, le=100, description="Number of items per page (max 100)"
    )
    event_type: Optional[LogEventType] = Field(
        None, description="Filter by event type"
    )
    user_id: Optional[UUID] = Field(None, description="Filter by user ID")
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    start_date: Optional[datetime] = Field(
        None, description="Filter by start date (ISO 8601 format)"
    )
    end_date: Optional[datetime] = Field(
        None, description="Filter by end date (ISO 8601 format)"
    )

    @field_validator("end_date")
    def validate_date_range(cls, v, info):
        # For Pydantic V2 compatibility
        if v is None:
            return v

        # Get the start_date from ValidationInfo
        start_date = None
        if hasattr(info, "data"):
            # Pydantic V2 approach
            start_date = info.data.get("start_date")

        if start_date and v < start_date:
            raise ValueError("end_date must be after start_date")
        return v

    class Config:
        json_schema_extra = {
            "examples": {
                "basic": {
                    "summary": "Basic pagination without filters",
                    "value": {"page": 1, "limit": 100},
                },
                "filter_by_event_and_user": {
                    "summary": "Filter logs by event type and user",
                    "value": {
                        "event_type": "USER_LOGIN",
                        "user_id": "11111111-1111-1111-1111-111111111111",
                        "page": 2,
                        "limit": 50,
                    },
                },
                "filter_by_date_range": {
                    "summary": "Filter logs by date range",
                    "value": {
                        "start_date": "2023-04-15T00:00:00Z",
                        "end_date": "2023-04-16T00:00:00Z",
                    },
                },
            }
        }


class ErrorResponse(BaseModel):
    error_code: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "INVALID_QUERY_PARAM",
                "message": "Invalid query parameter: role",
            }
        }


# Search/List Params
class OfferListQueryParams(BaseModel):
    search: Optional[str] = Field(
        None, description="Search by title or description"
    )
    category_id: Optional[int] = Field(
        None, description="Filter by category ID"
    )
    page: int = Field(1, gt=0, description="Page number, starting from 1")
    limit: int = Field(
        20, gt=0, le=100, description="Number of items per page (max 100)"
    )
    sort: str = Field(
        "created_at_desc",
        description="Sorting criteria (price_asc, price_desc, created_at_desc, relevance)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": {
                "basic": {
                    "summary": "Basic pagination without filters",
                    "value": {
                        "page": 1,
                        "limit": 20,
                        "sort": "created_at_desc",
                    },
                },
                "search_and_filter": {
                    "summary": "Search by keywords and filter by category",
                    "value": {
                        "search": "headphones",
                        "category_id": 2,
                        "sort": "price_desc",
                        "page": 1,
                        "limit": 50,
                    },
                },
            }
        }
    )
