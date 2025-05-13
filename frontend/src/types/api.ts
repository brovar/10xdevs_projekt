// UUID type for browser environment
export type UUID = string;

// Enum Types from DB
export enum UserRole {
  BUYER = "Buyer",
  SELLER = "Seller",
  ADMIN = "Admin"
}

export enum UserStatus {
  ACTIVE = "Active",
  INACTIVE = "Inactive",
  DELETED = "Deleted"
}

export enum OfferStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  SOLD = "sold",
  MODERATED = "moderated",
  ARCHIVED = "archived",
  DELETED = "deleted"
}

export enum OrderStatus {
  PENDING_PAYMENT = "pending_payment",
  PROCESSING = "processing",
  SHIPPED = "shipped",
  DELIVERED = "delivered",
  CANCELLED = "cancelled",
  FAILED = "failed"
}

export enum LogEventType {
  USER_LOGIN = "USER_LOGIN",
  USER_REGISTER = "USER_REGISTER",
  PASSWORD_CHANGE = "PASSWORD_CHANGE",
  USER_PROFILE_UPDATE = "USER_PROFILE_UPDATE",
  CATEGORY_LIST_VIEWED = "CATEGORY_LIST_VIEWED",
  OFFER_CREATE = "OFFER_CREATE",
  OFFER_EDIT = "OFFER_EDIT",
  OFFER_STATUS_CHANGE = "OFFER_STATUS_CHANGE",
  ORDER_PLACE_START = "ORDER_PLACE_START",
  ORDER_PLACE_SUCCESS = "ORDER_PLACE_SUCCESS",
  ORDER_PLACE_FAIL = "ORDER_PLACE_FAIL",
  ORDER_LIST_FAIL = "ORDER_LIST_FAIL",
  ORDER_DETAILS_FAIL = "ORDER_DETAILS_FAIL",
  PAYMENT_SUCCESS = "PAYMENT_SUCCESS",
  PAYMENT_FAIL = "PAYMENT_FAIL",
  OFFER_MODERATED = "OFFER_MODERATED",
  OFFER_MODERATION_ATTEMPT = "OFFER_MODERATION_ATTEMPT",
  OFFER_MODERATION_FAIL = "OFFER_MODERATION_FAIL",
  USER_ACTIVATED = "USER_ACTIVATED",
  USER_DEACTIVATED = "USER_DEACTIVATED",
  USER_BLOCK_ATTEMPT = "USER_BLOCK_ATTEMPT",
  USER_BLOCK_FAIL = "USER_BLOCK_FAIL",
  USER_DELETED = "USER_DELETED",
  USER_UNBLOCK_ATTEMPT = "USER_UNBLOCK_ATTEMPT",
  USER_UNBLOCK_FAIL = "USER_UNBLOCK_FAIL",
  SALES_LIST_FAIL = "SALES_LIST_FAIL",
  ORDER_STATUS_CHANGE = "ORDER_STATUS_CHANGE",
  ORDER_SHIP_FAIL = "ORDER_SHIP_FAIL",
  ORDER_DELIVER_FAIL = "ORDER_DELIVER_FAIL",
  PAYMENT_CALLBACK_SUCCESS = "PAYMENT_CALLBACK_SUCCESS",
  PAYMENT_CALLBACK_FAIL = "PAYMENT_CALLBACK_FAIL",
  ADMIN_LIST_USERS = "ADMIN_LIST_USERS",
  ADMIN_LIST_USERS_FAIL = "ADMIN_LIST_USERS_FAIL",
  ADMIN_GET_USER_DETAILS = "ADMIN_GET_USER_DETAILS",
  ADMIN_GET_USER_DETAILS_FAIL = "ADMIN_GET_USER_DETAILS_FAIL",
  ADMIN_LIST_OFFERS = "ADMIN_LIST_OFFERS",
  ADMIN_LIST_OFFERS_FAIL = "ADMIN_LIST_OFFERS_FAIL",
  OFFER_UNMODERATION_ATTEMPT = "OFFER_UNMODERATION_ATTEMPT",
  OFFER_UNMODERATED = "OFFER_UNMODERATED",
  OFFER_UNMODERATION_FAIL = "OFFER_UNMODERATION_FAIL",
  ADMIN_LIST_ORDERS = "ADMIN_LIST_ORDERS",
  ADMIN_LIST_ORDERS_SUCCESS = "ADMIN_LIST_ORDERS_SUCCESS",
  ADMIN_LIST_ORDERS_FAIL = "ADMIN_LIST_ORDERS_FAIL",
  ORDER_CANCEL_ATTEMPT = "ORDER_CANCEL_ATTEMPT",
  ORDER_CANCELLED = "ORDER_CANCELLED",
  ORDER_CANCEL_FAIL = "ORDER_CANCEL_FAIL",
  ADMIN_ACTION = "ADMIN_ACTION",
  ADMIN_ACTION_FAIL = "ADMIN_ACTION_FAIL"
}

// Base Models
interface PaginatedResponse {
  items: any[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// User DTOs
export interface UserDTO {
  id: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  first_name?: string | null;
  last_name?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface UserListResponse extends PaginatedResponse {
  items: UserDTO[];
}

export interface UserListQueryParams {
  page?: number;
  limit?: number;
  role?: UserRole;
  status?: UserStatus;
  search?: string;
}

// Category DTOs
export interface CategoryDTO {
  id: number;
  name: string;
}

// Offer DTOs
export interface SellerInfoDTO {
  id: string;
  first_name?: string | null;
  last_name?: string | null;
}

export interface OfferSummaryDTO {
  id: string;
  seller_id: string;
  category_id: number;
  title: string;
  price: string;
  image_filename?: string | null;
  quantity: number;
  status: OfferStatus;
  created_at: string;
}

export interface OfferDetailDTO extends OfferSummaryDTO {
  description?: string | null;
  updated_at?: string | null;
  seller: SellerInfoDTO;
  category: CategoryDTO;
}

export interface OfferListResponse extends PaginatedResponse {
  items: OfferSummaryDTO[];
}

export interface AdminOfferListQueryParams {
  search?: string;
  category_id?: number;
  seller_id?: string;
  status?: OfferStatus;
  sort?: string;
  page?: number;
  limit?: number;
}

// Order DTOs
export interface OrderItemDTO {
  id: number;
  offer_id: string;
  quantity: number;
  price_at_purchase: string;
  offer_title: string;
}

export interface OrderSummaryDTO {
  id: string;
  status: OrderStatus;
  total_amount: string;
  created_at: string;
  updated_at?: string | null;
}

export interface OrderDetailDTO {
  id: string;
  buyer_id: string;
  status: OrderStatus;
  created_at: string;
  updated_at?: string | null;
  items: OrderItemDTO[];
  total_amount: string;
}

export interface OrderListResponse extends PaginatedResponse {
  items: OrderSummaryDTO[];
}

export interface AdminOrderListQueryParams {
  page?: number;
  limit?: number;
  status?: OrderStatus;
  buyer_id?: string;
  seller_id?: string;
}

// Log DTOs
export interface LogDTO {
  id: number;
  event_type: LogEventType;
  user_id?: string | null;
  ip_address?: string | null;
  message: string;
  timestamp: string;
}

export interface LogListResponse extends PaginatedResponse {
  items: LogDTO[];
}

export interface AdminLogListQueryParams {
  page?: number;
  limit?: number;
  event_type?: LogEventType;
  user_id?: string;
  ip_address?: string;
  start_date?: string;
  end_date?: string;
}

export interface ErrorResponse {
  error_code: string;
  message: string;
} 