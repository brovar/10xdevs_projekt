/**
 * Maps order status to display values and CSS classes
 */
export const orderStatusMap = {
  pending_payment: { 
    display: 'Pending Payment', 
    className: 'bg-warning text-dark'
  },
  processing: { 
    display: 'Processing', 
    className: 'bg-info text-white'
  },
  shipped: { 
    display: 'Shipped', 
    className: 'bg-primary text-white'
  },
  delivered: { 
    display: 'Delivered', 
    className: 'bg-success text-white'
  },
  cancelled: { 
    display: 'Cancelled', 
    className: 'bg-danger text-white'
  },
  failed: { 
    display: 'Failed', 
    className: 'bg-danger text-white'
  },
  // Dla kompatybilności z istniejącą aplikacją
  completed: { 
    display: 'Completed', 
    className: 'bg-success text-white'
  },
  pending: { 
    display: 'Pending', 
    className: 'bg-warning text-dark'
  }
};

/**
 * Maps the API order data to the view model used in components
 * @param {Object} orderSummary - OrderSummaryDTO from API
 * @returns {Object} SaleItemVM for component usage
 */
export const mapOrderSummaryToSaleItemVM = (orderSummary) => {
  // Extract status from the order
  const { status } = orderSummary;
  
  // Define allowed status transitions
  const canChangeStatus = status === 'processing' || status === 'shipped';
  
  // Define next status options based on current status
  let nextStatusOptions = [];
  if (status === 'processing') {
    nextStatusOptions = [{ value: 'shipped', label: 'Mark as Shipped' }];
  } else if (status === 'shipped') {
    nextStatusOptions = [{ value: 'delivered', label: 'Mark as Delivered' }];
  }
  
  // Format date
  const createdAt = new Date(orderSummary.created_at).toLocaleString('en-US', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
  
  // Format currency
  const totalAmount = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(orderSummary.total_amount);
  
  // Create shortened display ID from UUID
  const displayId = orderSummary.id.split('-')[0];
  
  return {
    id: orderSummary.id,
    displayId,
    status,
    statusDisplay: orderStatusMap[status]?.display || status,
    statusClassName: orderStatusMap[status]?.className || 'bg-secondary',
    totalAmount,
    createdAt,
    canChangeStatus,
    nextStatusOptions,
  };
}; 