/**
 * Maps order status to display values and CSS classes
 */
export const orderStatusMap = {
  pending_payment: { 
    display: 'Oczekuje na płatność', 
    className: 'bg-warning text-dark'
  },
  processing: { 
    display: 'W trakcie realizacji', 
    className: 'bg-info text-white'
  },
  shipped: { 
    display: 'Wysłane', 
    className: 'bg-primary text-white'
  },
  delivered: { 
    display: 'Dostarczone', 
    className: 'bg-success text-white'
  },
  cancelled: { 
    display: 'Anulowane', 
    className: 'bg-danger text-white'
  },
  failed: { 
    display: 'Nieudane', 
    className: 'bg-danger text-white'
  },
  // Dla kompatybilności z istniejącą aplikacją
  completed: { 
    display: 'Zrealizowane', 
    className: 'bg-success text-white'
  },
  pending: { 
    display: 'Oczekujące', 
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
    nextStatusOptions = [{ value: 'shipped', label: 'Oznacz jako wysłane' }];
  } else if (status === 'shipped') {
    nextStatusOptions = [{ value: 'delivered', label: 'Oznacz jako dostarczone' }];
  }
  
  // Format date to Polish format
  const createdAt = new Date(orderSummary.created_at).toLocaleString('pl-PL', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
  
  // Format currency
  const totalAmount = new Intl.NumberFormat('pl-PL', {
    style: 'currency',
    currency: 'PLN'
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