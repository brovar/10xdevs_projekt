import React, { useState, useEffect, useCallback } from 'react';
import { Container, Row, Col, Alert, Spinner, Table, Badge } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';

/**
 * OrdersPage - User orders history page
 * 
 * This page displays a list of user's orders with basic information and status
 */
const OrdersPage = () => {
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // This is a placeholder. In a real implementation, this would call an API
  const fetchOrders = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Simulating API call delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Mock data for display purposes
      const mockOrders = [
        {
          id: 'ORD-2023-001',
          date: '2023-10-15',
          total: 129.99,
          status: 'completed',
          items: 3
        },
        {
          id: 'ORD-2023-002',
          date: '2023-11-05',
          total: 59.99,
          status: 'processing',
          items: 1
        },
        {
          id: 'ORD-2023-003',
          date: '2023-12-01',
          total: 89.99,
          status: 'pending',
          items: 2
        }
      ];
      
      setOrders(mockOrders);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
      setError('Nie udało się załadować historii zamówień. Spróbuj odświeżyć stronę.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  // Helper function to render status badge with appropriate color
  const renderStatusBadge = (status) => {
    let variant = 'secondary';
    let label = status;

    switch (status) {
      case 'completed':
        variant = 'success';
        label = 'Zrealizowane';
        break;
      case 'processing':
        variant = 'primary';
        label = 'W realizacji';
        break;
      case 'pending':
        variant = 'warning';
        label = 'Oczekujące';
        break;
      case 'cancelled':
        variant = 'danger';
        label = 'Anulowane';
        break;
      default:
        break;
    }

    return <Badge bg={variant}>{label}</Badge>;
  };

  return (
    <Container className="py-5">
      <h1 className="mb-4">Moje Zamówienia</h1>
      
      {isLoading ? (
        <div className="text-center py-5">
          <Spinner animation="border" role="status" variant="primary">
            <span className="visually-hidden">Ładowanie...</span>
          </Spinner>
          <p className="mt-3">Ładowanie historii zamówień...</p>
        </div>
      ) : error ? (
        <Alert variant="danger" className="mb-4">
          {error}
        </Alert>
      ) : orders.length === 0 ? (
        <Alert variant="info">
          Nie masz jeszcze żadnych zamówień. Przejdź do sklepu, aby złożyć pierwsze zamówienie.
        </Alert>
      ) : (
        <>
          <p>Poniżej znajduje się lista Twoich zamówień.</p>
          
          <Table responsive striped hover className="mt-4">
            <thead>
              <tr>
                <th>Numer zamówienia</th>
                <th>Data</th>
                <th>Liczba produktów</th>
                <th>Kwota</th>
                <th>Status</th>
                <th>Akcje</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(order => (
                <tr key={order.id}>
                  <td>{order.id}</td>
                  <td>{order.date}</td>
                  <td>{order.items}</td>
                  <td>{order.total.toFixed(2)} zł</td>
                  <td>{renderStatusBadge(order.status)}</td>
                  <td>
                    <button 
                      className="btn btn-sm btn-outline-primary"
                      onClick={() => alert(`Szczegóły zamówienia ${order.id} zostaną wdrożone w przyszłej wersji.`)}
                    >
                      Szczegóły
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      )}
    </Container>
  );
};

export default OrdersPage; 