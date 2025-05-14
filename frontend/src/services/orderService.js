import axios from './api';

/**
 * Fetch paginated list of orders for the current user
 * @param {number} page - Current page (1-based)
 * @param {number} limit - Number of items per page
 * @returns {Promise<OrderListResponseDTO>} - Paginated order list
 */
export const fetchOrderHistory = async (page = 1, limit = 10) => {
  try {
    console.log(`Fetching order history: page=${page}, limit=${limit}`);
    const response = await axios.get('/orders', {
      params: { page, limit }
    });
    console.log('Order history response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch order history:', error.response?.data || error);
    throw error;
  }
};

/**
 * Fetch detailed information about a specific order
 * @param {string} orderId - UUID of the order
 * @returns {Promise<OrderDetailDTO>} - Order details
 */
export const fetchOrderDetails = async (orderId) => {
  if (!orderId) {
    throw new Error('Order ID is required');
  }
  
  try {
    console.log(`Fetching order details for ID: ${orderId}`);
    
    // Log authentication headers for debugging
    const authHeaders = axios.defaults.headers.common;
    console.log('Auth headers being sent:', {
      ...authHeaders,
      Authorization: authHeaders.Authorization ? 'Bearer [FILTERED]' : undefined
    });
    
    const response = await axios.get(`/orders/${orderId}`);
    console.log('Order details response:', response.data);
    
    // Log important IDs for debugging access control
    if (response.data && response.data.buyer_id) {
      console.log('Order buyer_id from API:', response.data.buyer_id);
    }
    
    return response.data;
  } catch (error) {
    console.error(`Failed to fetch order ${orderId}:`, error.response?.data || error);
    
    // Log more detailed error information
    if (error.response) {
      console.error('Error response status:', error.response.status);
      console.error('Error response data:', error.response.data);
    }
    
    // Standardize error messages based on status code
    if (error.response) {
      const { status } = error.response;
      if (status === 403) {
        error.message = 'You do not have permission to view this order.';
      } else if (status === 404) {
        error.message = 'Order with the provided ID was not found.';
      } else if (status >= 500) {
        error.message = 'A server error occurred while loading the order.';
      }
    }
    
    throw error;
  }
}; 