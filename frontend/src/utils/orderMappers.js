/**
 * Map an order summary DTO from the API to a view model format
 * @param {Object} dto - The order summary DTO from the API
 * @returns {Object} - Formatted view model
 */
export const mapOrderSummaryToViewModel = (dto) => {
  // Create a shortened display ID from the UUID
  const displayId = `Zam. #${dto.id.substring(0, 8).toUpperCase()}`;
  
  // Format the date for display
  const createdAt = new Date(dto.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric'
  });
  
  // Format the amount with currency
  const totalAmount = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(parseFloat(dto.total_amount));
  
  // Get the number of items if available, or default to unknown
  const itemsCount = dto.items?.length || 0;
  
  return {
    id: dto.id,
    displayId,
    status: dto.status,
    totalAmount,
    createdAt,
    detailsLink: `/orders/${dto.id}`,
    itemsCount
  };
};

/**
 * Map a paginated API response to a pagination view model
 * @param {Object} response - The API response
 * @returns {Object} - Pagination view model
 */
export const mapPaginationData = (response) => {
  return {
    currentPage: response.page,
    totalPages: response.pages,
    totalItems: response.total,
    itemsPerPage: response.limit
  };
};

/**
 * Map an array of order summary DTOs to view models
 * @param {Array} items - Array of order summary DTOs
 * @returns {Array} - Array of view models
 */
export const mapOrderList = (items = []) => {
  return items.map(mapOrderSummaryToViewModel);
};

/**
 * Map a single order item DTO to a view model
 * @param {Object} dto - Order item DTO
 * @returns {Object} - Order item view model
 */
export const mapOrderItemToViewModel = (dto) => {
  // Convert string price to a number for calculations
  const priceAtPurchase = parseFloat(dto.price_at_purchase);
  
  // Calculate the item total
  const itemSum = priceAtPurchase * dto.quantity;
  
  // Format the prices for display
  const priceAtPurchaseFormatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(priceAtPurchase);
  
  const itemSumFormatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(itemSum);
  
  return {
    id: dto.id,
    offerId: dto.offer_id,
    offerTitle: dto.offer_title,
    quantity: dto.quantity,
    priceAtPurchase,
    priceAtPurchaseFormatted,
    itemSum,
    itemSumFormatted
  };
};

/**
 * Map an order detail DTO to a view model
 * @param {Object} dto - Order detail DTO
 * @returns {Object} - Order detail view model
 */
export const mapOrderDetailToViewModel = (dto) => {
  // Create a shortened display ID
  const displayId = `Zam. #${dto.id.substring(0, 8).toUpperCase()}`;
  
  // Format the date for display
  const createdAt = new Date(dto.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric'
  });
  
  // Format updated date if available
  const updatedAt = dto.updated_at
    ? new Date(dto.updated_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric'
      })
    : null;
  
  // Format the total amount
  const totalAmount = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(parseFloat(dto.total_amount));
  
  // Map the order items
  const items = dto.items.map(mapOrderItemToViewModel);
  
  return {
    id: dto.id,
    displayId,
    buyerId: dto.buyer_id,
    status: dto.status,
    createdAt,
    updatedAt,
    items,
    totalAmount
  };
}; 