import React, { useState, useEffect, useCallback } from 'react';
import { Container, Alert, Spinner, Row, Col, Card, Badge } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import axios from '../../services/api';

const MyOffersPage = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [offers, setOffers] = useState([]);
  const [error, setError] = useState(null);
  const { user } = useAuth();
  const { addError } = useNotifications();

  // Funkcja do pobierania ofert
  const fetchOffers = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('/seller/offers');
      setOffers(response.data.items || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching offers:', err);
      setError('Nie udało się pobrać ofert. Spróbuj ponownie później.');
      addError('Wystąpił błąd podczas ładowania ofert');
    } finally {
      setIsLoading(false);
    }
  }, [addError]);

  useEffect(() => {
    fetchOffers();
  }, [fetchOffers]);

  // Helper do renderowania statusu oferty jako Badge
  const renderStatusBadge = (status) => {
    let variant = 'secondary';
    switch (status) {
      case 'active':
        variant = 'success';
        break;
      case 'inactive':
        variant = 'warning';
        break;
      case 'sold':
        variant = 'info';
        break;
      case 'archived':
        variant = 'dark';
        break;
      case 'moderated':
        variant = 'danger';
        break;
      default:
        variant = 'secondary';
    }
    return <Badge bg={variant}>{status}</Badge>;
  };

  if (isLoading) {
    return (
      <Container className="py-4 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Ładowanie...</span>
        </Spinner>
      </Container>
    );
  }

  return (
    <Container className="py-4">
      <h1>Moje Oferty</h1>
      {error && (
        <Alert variant="danger">{error}</Alert>
      )}
      {!error && offers.length === 0 && (
        <Alert variant="info">
          Nie masz jeszcze żadnych ofert. Dodaj swoją pierwszą ofertę, aby zacząć sprzedawać!
        </Alert>
      )}
      
      {offers.length > 0 && (
        <Row>
          {offers.map(offer => (
            <Col key={offer.id} md={6} lg={4} className="mb-4">
              <Card>
                {offer.image_filename && (
                  <Card.Img 
                    variant="top" 
                    src={`http://localhost:8000/media/offers/${offer.id}/${offer.image_filename}`} 
                    alt={offer.title}
                    style={{ height: '200px', objectFit: 'cover' }}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = 'https://via.placeholder.com/300x200?text=Brak+zdjęcia';
                    }}
                  />
                )}
                <Card.Body>
                  <Card.Title>{offer.title}</Card.Title>
                  <Card.Text>
                    <strong>Cena:</strong> {offer.price} zł<br />
                    <strong>Ilość:</strong> {offer.quantity}<br />
                    <strong>Status:</strong> {renderStatusBadge(offer.status)}
                  </Card.Text>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </Container>
  );
};

export default MyOffersPage; 