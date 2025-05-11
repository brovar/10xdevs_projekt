import { api } from './api';

/**
 * Fetches list of categories
 * @returns {Promise<Array>} List of categories
 */
export const fetchCategories = async () => {
  try {
    const response = await api.get('/categories');
    return response.data;
  } catch (error) {
    console.error('Error fetching categories:', error);
    throw new Error('Nie udało się pobrać kategorii');
  }
};

/**
 * Creates a new offer
 * @param {FormData} formData - Form data containing offer details and image
 * @returns {Promise<Object>} Created offer data
 */
export const createOffer = async (formData) => {
  try {
    const response = await api.post('/offers', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error creating offer:', error);
    throw new Error(
      error.response?.data?.message || 'Nie udało się utworzyć oferty'
    );
  }
};

/**
 * Fetches list of seller's offers
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.limit - Number of items per page
 * @param {string} params.sort - Sort order
 * @returns {Promise<Object>} Paginated list of offers
 */
export const fetchSellerOffers = async (params = {}) => {
  try {
    const response = await api.get('/seller/offers', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching seller offers:', error);
    throw new Error('Nie udało się pobrać ofert');
  }
};

/**
 * Fetches details of a single offer
 * @param {string} offerId - ID of the offer to fetch
 * @returns {Promise<Object>} Offer details
 */
export const fetchOfferDetails = async (offerId) => {
  try {
    const response = await api.get(`/offers/${offerId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching offer details:', error);
    throw new Error('Nie udało się pobrać szczegółów oferty');
  }
};

/**
 * Updates an existing offer
 * @param {string} offerId - ID of the offer to update
 * @param {FormData} formData - Form data containing updated offer details
 * @returns {Promise<Object>} Updated offer data
 */
export const updateOffer = async (offerId, formData) => {
  try {
    const response = await api.put(`/offers/${offerId}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error updating offer:', error);
    throw new Error(
      error.response?.data?.message || 'Nie udało się zaktualizować oferty'
    );
  }
};

/**
 * Changes the status of an offer
 * @param {string} offerId - ID of the offer
 * @param {string} status - New status (active, inactive, etc.)
 * @returns {Promise<Object>} Updated offer data
 */
export const changeOfferStatus = async (offerId, status) => {
  try {
    const response = await api.patch(`/offers/${offerId}/status`, { status });
    return response.data;
  } catch (error) {
    console.error('Error changing offer status:', error);
    throw new Error(
      error.response?.data?.message || 'Nie udało się zmienić statusu oferty'
    );
  }
}; 