import React from 'react';
import { Alert, Container, Button } from 'react-bootstrap';
import { useRouteError, useNavigate } from 'react-router-dom';

const ErrorBoundary = () => {
  const error = useRouteError();
  const navigate = useNavigate();

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <Container className="py-5">
      <Alert variant="danger">
        <Alert.Heading>Wystąpił błąd!</Alert.Heading>
        <p>
          {error?.message || 'Coś poszło nie tak. Spróbuj ponownie później.'}
        </p>
        {error?.stack && process.env.NODE_ENV === 'development' && (
          <pre className="mt-3 p-3 bg-light text-dark" style={{ fontSize: '0.8rem' }}>
            {error.stack}
          </pre>
        )}
        <hr />
        <div className="d-flex justify-content-end">
          <Button variant="outline-danger" onClick={handleGoBack} className="me-2">
            Wróć
          </Button>
          <Button variant="danger" onClick={handleGoHome}>
            Strona główna
          </Button>
        </div>
      </Alert>
    </Container>
  );
};

export default ErrorBoundary; 