import React, { useState, useEffect, useCallback } from 'react';
import { Container, Alert, Spinner, Row, Col, Card, Badge, Button } from 'react-bootstrap';
// import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import { useNavigate } from 'react-router-dom';
import axios from '../../services/api';

const MyOffersPage = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [offers, setOffers] = useState([]);
  const [error, setError] = useState(null);
  const { addError } = useNotifications();
  const navigate = useNavigate();

  // Funkcja do pobierania ofert
  const fetchOffers = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('/seller/offers');
      setOffers(response.data.items || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching offers:', err);
      setError('Failed to fetch offers. Please try again later.');
      addError('An error occurred while loading offers');
    } finally {
      setIsLoading(false);
    }
  }, [addError]);

  // Funkcja do przekierowania do strony tworzenia oferty
  const handleCreateOffer = () => {
    navigate('/seller/offers/create');
  };

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
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </Container>
    );
  }

  return (
    <Container className="py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>My Offers</h1>
        <Button 
          variant="primary" 
          onClick={handleCreateOffer}
          className="d-flex align-items-center"
        >
          <i className="bi bi-plus-circle me-2"></i>
          Add new offer
        </Button>
      </div>
      
      {error && (
        <Alert variant="danger">{error}</Alert>
      )}
      {!error && offers.length === 0 && (
        <Alert variant="info">
          You don't have any offers yet. Add your first offer to start selling!
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
                      e.target.src = 'https://via.placeholder.com/300x200?text=No+image';
                    }}
                  />
                )}
                <Card.Body>
                  <Card.Title>{offer.title}</Card.Title>
                  <Card.Text>
                    <div className="mb-2">
                      <strong>Price:</strong> ${offer.price}<br />
                    </div>
                    <strong>Quantity:</strong> {offer.quantity}<br />
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