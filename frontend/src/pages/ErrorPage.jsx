import React from 'react';
import { Container, Button } from 'react-bootstrap';
import { Link } from 'react-router-dom';

const ErrorPage = () => {
  return (
    <Container className="py-5 text-center">
      <h2 className="mb-4">404 - Strona nie znaleziona</h2>
      <p className="lead mb-4">Przepraszamy, ale strona, której szukasz, nie istnieje.</p>
      <Button as={Link} to="/" variant="primary">
        Wróć na stronę główną
      </Button>
    </Container>
  );
};

export default ErrorPage; 