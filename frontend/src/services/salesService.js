import api from './api';

/**
 * Fetches the sales history for a seller with pagination and sorting
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number (starting from 1)
 * @param {number} params.limit - Number of items per page
 * @param {string} params.sort - Sort criteria (e.g., 'created_at_desc', 'created_at_asc', 'updated_at_desc', 
 *                              'updated_at_asc', 'total_amount_desc', 'total_amount_asc', 'status_desc', 'status_asc')
 * @returns {Promise<Object>} - Promise resolving to OrderListResponseDTO
 */
export const fetchSalesHistory = async (params = {}) => {
  const { page = 1, limit = 20, sort = 'created_at_desc' } = params;
  try {
    const response = await api.get('/seller/account/sales', {
      params: { page, limit, sort }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching sales history:', error);
    throw error;
  }
};

/**
 * Updates the status of an order (placeholder for future implementation)
 * Note: This function currently lacks a proper API endpoint
 * 
 * @param {string} orderId - UUID of the order to update
 * @param {Object} data - Update data
 * @param {string} data.status - New status ('shipped' or 'delivered')
 * @returns {Promise<Object>} - Promise resolving to updated order or error
 */
export const updateOrderStatus = async (orderId, data) => {
  try {
    // This is currently a mock implementation
    // In a real implementation, this would call an actual API endpoint
    console.warn("API endpoint for updating order status is not implemented yet");
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock successful response
    return {
      success: true,
      message: "Status update simulated. Actual API endpoint not implemented.",
      orderId,
      newStatus: data.status
    };
  } catch (error) {
    console.error('Error updating order status:', error);
    throw error;
  }
}; 