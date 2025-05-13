import React from 'react';
import PropTypes from 'prop-types';

const SellerInfoBadge = ({ sellerName }) => {
  return (
    <span 
      className="badge bg-light text-dark border"
      aria-label={`Sprzedawca: ${sellerName}`}
    >
      <i className="bi bi-person-circle me-1"></i>
      {sellerName}
    </span>
  );
};

SellerInfoBadge.propTypes = {
  sellerName: PropTypes.string.isRequired
};

export default SellerInfoBadge; 