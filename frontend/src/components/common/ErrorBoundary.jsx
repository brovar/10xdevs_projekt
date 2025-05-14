import React from 'react';
import { useRouteError } from 'react-router-dom';
import PropTypes from 'prop-types';

const ErrorBoundary = ({ resetErrorBoundary }) => {
  const error = useRouteError();
  
  return (
    <div className="container py-5 text-center">
      <div className="alert alert-danger">
        <h2>An error occurred</h2>
        <p>We're sorry, something went wrong.</p>
        <details className="mt-3">
          <summary>Error details</summary>
          <pre className="mt-2 text-start bg-light p-3 rounded">
            {error?.message || 'Unknown error'}
          </pre>
        </details>
        {resetErrorBoundary && (
          <button 
            className="btn btn-primary mt-3"
            onClick={resetErrorBoundary}
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
};

ErrorBoundary.propTypes = {
  resetErrorBoundary: PropTypes.func
};

export default ErrorBoundary;