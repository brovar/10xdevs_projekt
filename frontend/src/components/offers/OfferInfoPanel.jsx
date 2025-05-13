import React from 'react';
import PropTypes from 'prop-types';
import StatusBadge from '../shared/StatusBadge';
import SellerInfoBadge from './SellerInfoBadge';

const OfferInfoPanel = ({ offer }) => {
  if (!offer) return null;

  // Format the creation date
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pl-PL');
  };

  return (
    <div className="offer-info">
      <div className="d-flex align-items-start justify-content-between mb-2">
        <h1 className="mb-0">{offer.title}</h1>
        <StatusBadge text={offer.statusDisplay} className={offer.statusClassName} />
      </div>
      
      <p className="h3 text-primary my-3">{offer.priceFormatted}</p>
      
      <div className="mb-4">
        <h4 className="mb-2">Opis produktu</h4>
        <p className="mb-4">
          {offer.description || 'Brak opisu dla tego produktu.'}
        </p>
      </div>
      
      <div className="mb-3">
        <h5>Szczegóły</h5>
        <ul className="list-group list-group-flush">
          <li className="list-group-item d-flex justify-content-between align-items-center">
            <span>Kategoria:</span>
            <span className="fw-bold">{offer.categoryName}</span>
          </li>
          
          <li className="list-group-item d-flex justify-content-between align-items-center">
            <span>Sprzedawca:</span>
            <SellerInfoBadge sellerName={offer.sellerName} />
          </li>
          
          <li className="list-group-item d-flex justify-content-between align-items-center">
            <span>Dostępna ilość:</span>
            <span 
              className={`fw-bold ${offer.quantity > 0 ? 'text-success' : 'text-danger'}`}
              aria-label={`Dostępna ilość: ${offer.quantity}`}
            >
              {offer.quantity} szt.
            </span>
          </li>
          
          {offer.createdAt && (
            <li className="list-group-item d-flex justify-content-between align-items-center">
              <span>Data dodania:</span>
              <span>{formatDate(offer.createdAt)}</span>
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

OfferInfoPanel.propTypes = {
  offer: PropTypes.shape({
    title: PropTypes.string.isRequired,
    statusDisplay: PropTypes.string.isRequired,
    statusClassName: PropTypes.string.isRequired,
    priceFormatted: PropTypes.string.isRequired,
    description: PropTypes.string,
    categoryName: PropTypes.string.isRequired,
    sellerName: PropTypes.string.isRequired,
    quantity: PropTypes.number.isRequired,
    createdAt: PropTypes.string
  })
};

export default OfferInfoPanel; 