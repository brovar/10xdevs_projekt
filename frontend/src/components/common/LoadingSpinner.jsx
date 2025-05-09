import React from 'react';
import { Spinner, Container } from 'react-bootstrap';

const LoadingSpinner = ({ message = 'Ładowanie...' }) => {
  return (
    <Container className="d-flex flex-column align-items-center justify-content-center py-5">
      <Spinner animation="border" role="status" className="mb-3">
        <span className="visually-hidden">Ładowanie...</span>
      </Spinner>
      <p className="text-center">{message}</p>
    </Container>
  );
};

export default LoadingSpinner; 