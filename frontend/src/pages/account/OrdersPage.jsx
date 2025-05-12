import React, { useState, useEffect, useCallback } from 'react';
import { Container, Alert, Spinner } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import { useSearchParams } from 'react-router-dom';

// Components
import OrdersList from '../../components/orders/OrdersList';
import Pagination from '../../components/common/Pagination';

// Services & Utils
import { fetchOrderHistory } from '../../services/orderService';
import { mapOrderList, mapPaginationData } from '../../utils/orderMappers';

const ITEMS_PER_PAGE = 10;

/**
 * OrdersPage - User orders history page
 * 
 * This page displays a list of user's orders with basic information and status
 */
const OrdersPage = () => {
  const { } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Get current page from URL or default to 1
  const currentPageParam = searchParams.get('page');
  const initialPage = currentPageParam ? parseInt(currentPageParam, 10) : 1;
  
  // State
  const [orders, setOrders] = useState([]);
  const [paginationData, setPaginationData] = useState({
    currentPage: initialPage,
    totalPages: 1,
    totalItems: 0,
    itemsPerPage: ITEMS_PER_PAGE
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch orders from API based on current page
  const fetchOrders = useCallback(async (page = 1) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetchOrderHistory(page, ITEMS_PER_PAGE);
      
      // Map response data to view models
      const mappedOrders = mapOrderList(response.items || []);
      setOrders(mappedOrders);
      
      // Set pagination data
      setPaginationData(mapPaginationData(response));
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      setError('Nie udało się załadować historii zamówień. Spróbuj odświeżyć stronę.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Handle page change
  const handlePageChange = useCallback((newPage) => {
    // Update URL to reflect new page
    setSearchParams({ page: newPage.toString() });
  }, [setSearchParams]);

  // Fetch orders when page changes
  useEffect(() => {
    fetchOrders(paginationData.currentPage);
  }, [paginationData.currentPage, fetchOrders]);

  // Update currentPage when URL changes
  useEffect(() => {
    const page = searchParams.get('page');
    if (page) {
      const pageNumber = parseInt(page, 10);
      if (pageNumber !== paginationData.currentPage) {
        setPaginationData(prev => ({ ...prev, currentPage: pageNumber }));
      }
    } else {
      setPaginationData(prev => ({ ...prev, currentPage: 1 }));
    }
  }, [searchParams, paginationData.currentPage]);

  return (
    <Container className="py-5">
      <h1 className="mb-4">Moje Zamówienia</h1>
      
      {/* Loading state */}
      {isLoading && orders.length === 0 && (
        <div className="text-center py-5">
          <Spinner animation="border" role="status" variant="primary">
            <span className="visually-hidden">Ładowanie...</span>
          </Spinner>
          <p className="mt-3">Ładowanie historii zamówień...</p>
        </div>
      )}
      
      {/* Error state */}
      {error && (
        <Alert variant="danger" className="mb-4">
          {error}
        </Alert>
      )}
      
      {/* Empty state */}
      {!isLoading && !error && orders.length === 0 && (
        <Alert variant="info">
          Nie masz jeszcze żadnych zamówień. Przejdź do sklepu, aby złożyć pierwsze zamówienie.
        </Alert>
      )}
      
      {/* Orders list */}
      {!error && orders.length > 0 && (
        <>
          <p>Poniżej znajduje się lista Twoich zamówień.</p>
          
          <OrdersList 
            orders={orders} 
            isLoading={isLoading}
          />
          
          <Pagination 
            currentPage={paginationData.currentPage} 
            totalPages={paginationData.totalPages}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </Container>
  );
};

export default OrdersPage; 