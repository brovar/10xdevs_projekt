import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Container, Alert, Spinner, Button } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';

// Components
import OrderDetailsPanel from '../../components/orders/OrderDetailsPanel';
import ItemsListInOrder from '../../components/orders/ItemsListInOrder';

// Services & Utils
import { fetchOrderDetails } from '../../services/orderService';
import { mapOrderDetailToViewModel } from '../../utils/orderMappers';

/**
 * OrderDetailPage - Displays detailed information about a specific order
 * 
 * This page shows the order information and the list of items in the order
 */
const OrderDetailPage = () => {
  const { orderId } = useParams();
  const { user } = useAuth();
  
  // State
  const [order, setOrder] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch order details from API
  const fetchOrder = useCallback(async () => {
    if (!orderId) {
      setError('Order ID is required');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    
    try {
      // Log user information for debugging
      console.log('Current user data:', user);
      
      // Get order details from API
      const response = await fetchOrderDetails(orderId);
      console.log('Order details raw response:', response);
      
      // Map response data to view model
      const orderViewModel = mapOrderDetailToViewModel(response);
      console.log('Mapped order view model:', orderViewModel);
      
      // We will skip the user check here and let the backend handle the authorization
      // This way if the API returns data, we trust it's authorized to view it
      setOrder(orderViewModel);
    } catch (error) {
      console.error('Failed to fetch order details:', error);
      setError(error.message || 'Failed to load order details.');
    } finally {
      setIsLoading(false);
    }
  }, [orderId, user]);

  // Fetch order details when component mounts or orderId changes
  useEffect(() => {
    fetchOrder();
  }, [fetchOrder]);

  return (
    <Container className="py-5">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="mb-0">
          {order ? `Order Details ${order.displayId}` : 'Order Details'}
        </h1>
        <Link to="/orders" className="btn btn-outline-secondary">
          &larr; Back to Order History
        </Link>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="text-center py-5">
          <Spinner animation="border" role="status" variant="primary">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
          <p className="mt-3">Loading order details...</p>
        </div>
      )}
      
      {/* Error state */}
      {error && (
        <Alert variant="danger" className="mb-4">
          <Alert.Heading>An error occurred</Alert.Heading>
          <p>{error}</p>
          <hr />
          <div className="d-flex justify-content-end">
            <Button 
              variant="outline-danger" 
              onClick={fetchOrder}
            >
              Try Again
            </Button>
          </div>
        </Alert>
      )}
      
      {/* Order details */}
      {!isLoading && !error && order && (
        <>
          <OrderDetailsPanel order={order} />
          
          <h2 className="mt-5 mb-3">Products in Order</h2>
          <ItemsListInOrder items={order.items} />
        </>
      )}
    </Container>
  );
};

export default OrderDetailPage; 