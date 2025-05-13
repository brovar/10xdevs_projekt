import React from 'react';
import PropTypes from 'prop-types';

const LoadingSpinner = ({ message = 'Ładowanie...', size = 'md' }) => {
  // Define spinner sizes
  const spinnerSizes = {
    sm: 'spinner-border-sm',
    md: '',
    lg: 'spinner-border-lg'
  };

  return (
    <div className="d-flex flex-column align-items-center justify-content-center py-5">
      <div 
        className={`spinner-border text-primary ${spinnerSizes[size]}`} 
        role="status"
        aria-hidden="true"
      >
        <span className="visually-hidden">Ładowanie...</span>
      </div>
      {message && <p className="mt-3 text-center">{message}</p>}
    </div>
  );
};

LoadingSpinner.propTypes = {
  message: PropTypes.string,
  size: PropTypes.oneOf(['sm', 'md', 'lg'])
};

export default LoadingSpinner; 