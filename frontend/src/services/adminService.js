import axios from 'axios';

// Configure axios instance specifically for admin endpoints
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Clean empty string parameters from the request to avoid validation errors
const cleanParams = (params) => {
  if (!params) return params;
  
  const cleanedParams = {};
  
  // Copy only non-empty parameters
  Object.keys(params).forEach(key => {
    if (params[key] !== '' && params[key] !== null && params[key] !== undefined) {
      cleanedParams[key] = params[key];
    }
  });
  
  return cleanedParams;
};

// CSRF token handling for POST requests
const addCsrfToken = () => {
  // In a real app, you might get this from a cookie or a specific endpoint
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  if (csrfToken) {
    api.defaults.headers.common['X-CSRF-Token'] = csrfToken;
  }
};

// Admin Users API
export const adminUsersApi = {
  // Get users list
  getUsers: async (params) => {
    const cleanedParams = cleanParams(params);
    const response = await api.get('/admin/users', { params: cleanedParams });
    return response.data;
  },

  // Get user details
  getUserDetails: async (userId) => {
    const response = await api.get(`/admin/users/${userId}`);
    return response.data;
  },

  // Block user
  blockUser: async (userId) => {
    addCsrfToken();
    const response = await api.post(`/admin/users/${userId}/block`);
    return response.data;
  },

  // Unblock user
  unblockUser: async (userId) => {
    addCsrfToken();
    const response = await api.post(`/admin/users/${userId}/unblock`);
    return response.data;
  },
};

// Admin Offers API
export const adminOffersApi = {
  // Get offers list
  getOffers: async (params) => {
    const cleanedParams = cleanParams(params);
    const response = await api.get('/admin/offers', { params: cleanedParams });
    return response.data;
  },

  // Moderate offer
  moderateOffer: async (offerId) => {
    addCsrfToken();
    const response = await api.post(`/admin/offers/${offerId}/moderate`);
    return response.data;
  },

  // Unmoderate offer
  unmoderateOffer: async (offerId) => {
    addCsrfToken();
    const response = await api.post(`/admin/offers/${offerId}/unmoderate`);
    return response.data;
  },
};

// Admin Orders API
export const adminOrdersApi = {
  // Get orders list
  getOrders: async (params) => {
    const cleanedParams = cleanParams(params);
    const response = await api.get('/admin/orders', { params: cleanedParams });
    return response.data;
  },

  // Get order details
  getOrderDetails: async (orderId) => {
    const response = await api.get(`/admin/orders/${orderId}`);
    return response.data;
  },

  // Cancel order
  cancelOrder: async (orderId) => {
    addCsrfToken();
    const response = await api.post(`/admin/orders/${orderId}/cancel`);
    return response.data;
  },
};

// Admin Logs API
export const adminLogsApi = {
  // Get logs list
  getLogs: async (params) => {
    const cleanedParams = cleanParams(params);
    const response = await api.get('/admin/logs', { params: cleanedParams });
    return response.data;
  },
}; 