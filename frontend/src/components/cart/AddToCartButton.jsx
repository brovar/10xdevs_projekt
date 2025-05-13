import React from 'react';
import PropTypes from 'prop-types';

const AddToCartButton = ({ offerId, offerTitle, isDisabled, onClick }) => {
  const handleClick = () => {
    if (!isDisabled && onClick) {
      onClick(offerId, offerTitle);
    }
  };

  return (
    <button
      type="button"
      className="btn btn-primary btn-lg d-flex align-items-center justify-content-center w-100"
      onClick={handleClick}
      disabled={isDisabled}
      aria-label={`Dodaj ${offerTitle} do koszyka`}
    >
      <i className="bi bi-cart-plus-fill me-2"></i>
      Dodaj do koszyka
    </button>
  );
};

AddToCartButton.propTypes = {
  offerId: PropTypes.string.isRequired,
  offerTitle: PropTypes.string.isRequired,
  isDisabled: PropTypes.bool,
  onClick: PropTypes.func.isRequired
};

AddToCartButton.defaultProps = {
  isDisabled: false
};

export default AddToCartButton; 