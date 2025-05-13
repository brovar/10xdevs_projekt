import { UserRole, UserStatus, OfferStatus, OrderStatus, LogEventType } from './api';

/**
 * Definition for a tab in the admin dashboard
 */
export interface TabDefinition {
  key: string;
  title: string;
  component: React.FC;
}

/**
 * Common pagination data structure used across components
 */
export interface PaginationData {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  limit: number;
}

/**
 * Filter state for Users Management tab
 */
export interface UserFiltersState {
  search?: string;
  role?: string;
  status?: string;
  page: number;
  limit: number;
}

/**
 * Filter state for Offers Management tab
 */
export interface OfferFiltersState {
  search?: string;
  category_id?: number;
  seller_id?: string;
  status?: string;
  sort: string;
  page: number;
  limit: number;
}

/**
 * Filter state for Orders Management tab
 */
export interface OrderFiltersState {
  status?: string;
  buyer_id?: string;
  seller_id?: string;
  page: number;
  limit: number;
}

/**
 * Filter state for Logs Viewer tab
 */
export interface LogFiltersState {
  event_type?: string;
  user_id?: string;
  ip_address?: string;
  start_date?: string;
  end_date?: string;
  page: number;
  limit: number;
}

/**
 * State for confirmation modals
 */
export interface ConfirmActionState {
  type: 'block_user' | 'unblock_user' | 'moderate_offer' | 'unmoderate_offer' | 'cancel_order';
  id: string;
  additionalInfo?: string;
}

/**
 * Error state structure
 */
export interface ApiError {
  message: string;
  code?: string;
  status?: number;
}

// Action result
export interface ActionResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
} 