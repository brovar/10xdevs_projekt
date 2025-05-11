import React from 'react';
import PropTypes from 'prop-types';

/**
 * Component for displaying validation error messages
 * 
 * @param {Object} props - Component props
 * @param {string} [props.message] - Error message to display
 * @returns {JSX.Element|null} - Rendered component or null if no message
 */
const ValidationError = ({ message }) => {
  if (!message) {
    return null;
  }
  
  return (
    <div 
      className="alert alert-danger mt-3" 
      role="alert" 
      aria-live="polite"
    >
      {message}
    </div>
  );
};

ValidationError.propTypes = {
  message: PropTypes.string
};

export default ValidationError; 