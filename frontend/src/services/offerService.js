import { api } from './api';

/**
 * Fetches list of categories
 * @returns {Promise<Array>} List of categories
 */
export const fetchCategories = async () => {
  try {
    // First try to get categories from the API
    const response = await api.get('/categories');
    return response.data;
  } catch (error) {
    console.error('Error fetching categories:', error);
    
    // Fallback to mock data if the API fails
    if (process.env.NODE_ENV === 'development') {
      console.warn('Falling back to mock data for categories');
      return {
        items: [
          { id: 1, name: "Electronics" },
          { id: 2, name: "Books" },
          { id: 3, name: "Clothing" },
          { id: 4, name: "Home" },
          { id: 5, name: "Games" }
        ]
      };
    }
    
    throw new Error('Nie udało się pobrać kategorii');
  }
};

/**
 * Fetches paginated list of offers with optional filters
 * @param {Object} params - Query parameters
 * @param {string} [params.search] - Search term for offer title/description
 * @param {number} [params.category_id] - Filter by category ID
 * @param {number} [params.page=1] - Page number
 * @param {number} [params.limit=20] - Number of items per page
 * @param {string} [params.sort='created_at_desc'] - Sort order
 * @returns {Promise<Object>} Paginated list of offers
 */
export const fetchOffers = async (params = {}) => {
  try {
    // Use POST request to /offers/search endpoint which we implemented in the backend
    const response = await api.post('/offers/search', {
      search: params.search,
      category_id: params.category_id ? parseInt(params.category_id) : undefined,
      page: params.page || 1,
      limit: params.limit || 20,
      sort: params.sort || 'created_at_desc'
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching offers:', error);
    
    // Fallback to mock data if the API fails
    if (process.env.NODE_ENV === 'development') {
      console.warn('Falling back to mock data for offers');
      return getMockOffers(params);
    }
    
    throw new Error('Nie udało się pobrać ofert');
  }
};

/**
 * Helper function to provide mock data when the API is unavailable
 * @private
 */
const getMockOffers = (params = {}) => {
  const mockOffers = [
    {
      id: "550e8400-e29b-41d4-a716-446655440000",
      title: "PlayStation 5",
      description: "Brand new PlayStation 5 console with controller",
      price: "2499.99",
      image_filename: null,
      category_id: 1,
      quantity: 5,
      status: "active",
      created_at: "2025-05-10T12:00:00Z",
      seller_id: "550e8400-e29b-41d4-a716-446655440001"
    },
    {
      id: "550e8400-e29b-41d4-a716-446655440002",
      title: "The Lord of the Rings",
      description: "Complete trilogy book set",
      price: "199.99",
      image_filename: null,
      category_id: 2,
      quantity: 10,
      status: "active",
      created_at: "2025-05-09T10:00:00Z",
      seller_id: "550e8400-e29b-41d4-a716-446655440001"
    },
    {
      id: "550e8400-e29b-41d4-a716-446655440003",
      title: "Nike Running Shoes",
      description: "Premium running shoes size 42",
      price: "299.99",
      image_filename: null,
      category_id: 3,
      quantity: 3,
      status: "active",
      created_at: "2025-05-08T14:30:00Z",
      seller_id: "550e8400-e29b-41d4-a716-446655440004"
    }
  ];

  // Filter by search term if provided
  let filteredOffers = [...mockOffers];
  if (params.search) {
    const searchTerm = params.search.toLowerCase();
    filteredOffers = filteredOffers.filter(
      offer => 
        offer.title.toLowerCase().includes(searchTerm) || 
        (offer.description && offer.description.toLowerCase().includes(searchTerm))
    );
  }

  // Filter by category if provided
  if (params.category_id) {
    filteredOffers = filteredOffers.filter(
      offer => offer.category_id === parseInt(params.category_id)
    );
  }

  // Sort offers
  if (params.sort === 'price_asc') {
    filteredOffers.sort((a, b) => parseFloat(a.price) - parseFloat(b.price));
  } else if (params.sort === 'price_desc') {
    filteredOffers.sort((a, b) => parseFloat(b.price) - parseFloat(a.price));
  } else {
    // Default to created_at_desc
    filteredOffers.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }

  // Paginate
  const page = params.page || 1;
  const limit = params.limit || 20;
  const startIndex = (page - 1) * limit;
  const endIndex = page * limit;
  const paginatedOffers = filteredOffers.slice(startIndex, endIndex);

  return {
    items: paginatedOffers,
    total: filteredOffers.length,
    page: page,
    limit: limit,
    pages: Math.ceil(filteredOffers.length / limit)
  };
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
    // First try to get the offer details using the search API
    try {
      console.log(`Fetching offer details for ID: ${offerId}`);
      
      // Use the offers/search endpoint with pagination
      const response = await api.post('/offers/search', {
        page: 1,
        limit: 20
      });
      
      console.log('Search response:', response.data);
      
      // If we got results, find the specific offer by ID
      if (response.data && response.data.items && response.data.items.length > 0) {
        const offer = response.data.items.find(item => item.id === offerId);
        
        if (offer) {
          console.log('Found offer in search results:', offer);
          
          // Fetch categories to get category name
          const categoriesResponse = await fetchCategories();
          const categories = categoriesResponse.items || [];
          
          const category = categories.find(cat => cat.id === offer.category_id) || {
            id: offer.category_id,
            name: getCategoryNameById(offer.category_id)
          };
          
          // Enrich the offer data with seller and category information
          return {
            ...offer,
            seller: {
              id: offer.seller_id,
              first_name: "Seller",
              last_name: `#${offer.seller_id.substring(0, 6)}`
            },
            category: category
          };
        } else {
          console.warn(`Offer with ID ${offerId} not found in search results`);
        }
      }
      
      // If no results or offer not found, continue to fallback
      console.warn('Using fallback for offer details');
    } catch (apiError) {
      console.warn('API error when fetching offer details:', apiError);
    }
    
    // Fallback to mock data
    console.log('Using mock data for offer details');
    const mockOffers = {
      "550e8400-e29b-41d4-a716-446655440000": {
        id: "550e8400-e29b-41d4-a716-446655440000",
        title: "PlayStation 5",
        description: "Brand new PlayStation 5 console with controller. Includes two games and an extra controller. Perfect condition, never used.",
        price: "2499.99",
        image_filename: null,
        category_id: 1,
        quantity: 5,
        status: "active",
        created_at: "2025-05-10T12:00:00Z",
        updated_at: null,
        seller_id: "550e8400-e29b-41d4-a716-446655440001",
        seller: {
          id: "550e8400-e29b-41d4-a716-446655440001",
          first_name: "John",
          last_name: "Seller"
        },
        category: {
          id: 1,
          name: "Electronics"
        }
      },
      "550e8400-e29b-41d4-a716-446655440002": {
        id: "550e8400-e29b-41d4-a716-446655440002",
        title: "The Lord of the Rings",
        description: "Complete trilogy book set in hardcover. Includes beautiful illustrations and maps. Like new condition.",
        price: "199.99",
        image_filename: null,
        category_id: 2,
        quantity: 10,
        status: "active",
        created_at: "2025-05-09T10:00:00Z",
        updated_at: null,
        seller_id: "550e8400-e29b-41d4-a716-446655440001",
        seller: {
          id: "550e8400-e29b-41d4-a716-446655440001",
          first_name: "John",
          last_name: "Seller"
        },
        category: {
          id: 2,
          name: "Books"
        }
      },
      "550e8400-e29b-41d4-a716-446655440003": {
        id: "550e8400-e29b-41d4-a716-446655440003",
        title: "Nike Running Shoes",
        description: "Premium running shoes size 42. Very comfortable for long distance running. Used only a few times, excellent condition.",
        price: "299.99",
        image_filename: null,
        category_id: 3,
        quantity: 3,
        status: "active",
        created_at: "2025-05-08T14:30:00Z",
        updated_at: null,
        seller_id: "550e8400-e29b-41d4-a716-446655440004",
        seller: {
          id: "550e8400-e29b-41d4-a716-446655440004",
          first_name: "Alice",
          last_name: "Vendor"
        },
        category: {
          id: 3,
          name: "Clothing"
        }
      }
    };

    const offer = mockOffers[offerId];
    
    if (!offer) {
      throw new Error('Offer not found');
    }
    
    return offer;
  } catch (error) {
    console.error('Error fetching offer details:', error);
    throw error;
  }
};

// Helper function to get category name by ID
const getCategoryNameById = (categoryId) => {
  const categoryMap = {
    1: "Electronics",
    2: "Books",
    3: "Clothing",
    4: "Home",
    5: "Games"
  };
  return categoryMap[categoryId] || "Unknown Category";
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