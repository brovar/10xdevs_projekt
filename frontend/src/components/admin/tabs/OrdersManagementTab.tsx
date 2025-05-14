import React, { useState, useCallback } from 'react';
import useAdminData from '../../../hooks/useAdminData.ts';
import { adminOrdersApi } from '../../../services/adminService.ts';
import { OrderFiltersState, PaginationData, ConfirmActionState } from '../../../types/viewModels.ts';
import { OrderSummaryDTO, OrderListResponse, AdminOrderListQueryParams, OrderStatus } from '../../../types/api.ts';

import OrderFiltersComponent from './OrderFiltersComponent.tsx';
import AdminOrderListTable from './AdminOrderListTable.tsx';
import PaginationComponent from '../../shared/PaginationComponent.tsx';
import ConfirmationModal from '../../shared/ConfirmationModal.tsx';
import LoadingSpinner from '../../shared/LoadingSpinner.tsx';
import ErrorMessageDisplay from '../../shared/ErrorMessageDisplay.tsx';

const OrdersManagementTab: React.FC = () => {
  // Modal state for confirmation actions
  const [confirmAction, setConfirmAction] = useState<ConfirmActionState | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [actionError, setActionError] = useState<string | null>(null);
  
  // Default filters
  const initialFilters: OrderFiltersState = {
    page: 1,
    limit: 10
  };

  // Convert UI filter state to API query params
  const convertFiltersToQueryParams = useCallback(
    (filters: OrderFiltersState): AdminOrderListQueryParams => {
      const queryParams: AdminOrderListQueryParams = {
        page: filters.page,
        limit: filters.limit
      };

      if (filters.status) {
        // Type assertion since we know it's a valid OrderStatus from the UI
        queryParams.status = filters.status as OrderStatus;
      }

      if (filters.buyer_id) {
        queryParams.buyer_id = filters.buyer_id;
      }

      if (filters.seller_id) {
        queryParams.seller_id = filters.seller_id;
      }

      return queryParams;
    },
    []
  );

  // Extract items and pagination data from API response
  const extractItems = useCallback((response: OrderListResponse): OrderSummaryDTO[] => {
    return response.items;
  }, []);

  const extractPaginationData = useCallback((response: OrderListResponse): PaginationData => {
    return {
      currentPage: response.page,
      totalPages: response.pages,
      totalItems: response.total,
      limit: response.limit
    };
  }, []);

  // Use admin data hook for fetching orders with the conversion function
  const { 
    items: orders, 
    isLoading, 
    error, 
    paginationData, 
    queryParams,
    handlePageChange,
    handleFiltersChange,
    fetchData
  } = useAdminData<OrderFiltersState, OrderListResponse, OrderSummaryDTO>({
    fetchFunction: (filters) => adminOrdersApi.getOrders(convertFiltersToQueryParams(filters)),
    initialParams: initialFilters,
    extractItems,
    extractPaginationData
  });

  // Handler for cancelling an order
  const handleCancelOrder = useCallback((orderId: string) => {
    // Reset any previous errors
    setActionError(null);
    
    // Find order info for the confirmation message
    const orderToCancel = orders.find(order => order.id === orderId);
    if (!orderToCancel) return;

    setConfirmAction({
      type: 'cancel_order',
      id: orderId,
      additionalInfo: `Are you sure you want to cancel order ${orderId.slice(0, 8)}...?`
    });
  }, [orders]);

  // Handle confirmation for cancel action
  const handleConfirmAction = useCallback(async () => {
    if (!confirmAction) return;

    setIsProcessing(true);
    setActionError(null);

    try {
      if (confirmAction.type === 'cancel_order') {
        await adminOrdersApi.cancelOrder(confirmAction.id);
        // Refresh the data after action is completed
        fetchData();
      }
    } catch (err) {
      console.error('Action failed:', err);
      
      // Set error message for the modal
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'An unexpected error occurred while cancelling the order';
      
      setActionError(errorMessage);
      
      // Don't close the modal on error so user can see the error message
      return;
    } finally {
      setIsProcessing(false);
      
      // Only close the modal if there's no error
      if (!actionError) {
        setConfirmAction(null);
      }
    }
  }, [confirmAction, fetchData, actionError]);

  // Close confirmation modal
  const handleCancelAction = () => {
    setConfirmAction(null);
    setActionError(null);
    setIsProcessing(false);
  };

  return (
    <div className="orders-management-tab">
      <h2 className="mb-4">Orders Management</h2>
      
      {/* Filters */}
      <OrderFiltersComponent 
        currentFilters={queryParams}
        onFilterChange={handleFiltersChange}
      />
      
      {/* Loading state */}
      {isLoading && <LoadingSpinner text="Loading orders..." />}
      
      {/* Error state */}
      {error && !isLoading && (
        <ErrorMessageDisplay error={error} className="mb-4" />
      )}
      
      {/* Orders table */}
      {!isLoading && !error && (
        <>
          <AdminOrderListTable 
            orders={orders} 
            onCancel={handleCancelOrder}
          />
          
          {/* No orders message */}
          {orders.length === 0 && !isLoading && (
            <div className="alert alert-info" role="status">
              No orders matching search criteria.
            </div>
          )}
          
          {/* Pagination */}
          {paginationData && paginationData.totalItems > 0 && (
            <div className="mt-4">
              <PaginationComponent 
                paginationInfo={paginationData}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </>
      )}
      
      {/* Confirmation Modal */}
      {confirmAction && (
        <ConfirmationModal
          isOpen={true}
          title="Cancel Order"
          message={confirmAction.additionalInfo || ''}
          onConfirm={handleConfirmAction}
          onCancel={handleCancelAction}
          confirmButtonText="Cancel Order"
          variant="danger"
          isProcessing={isProcessing}
          error={actionError}
        />
      )}
    </div>
  );
};

export default OrdersManagementTab; 