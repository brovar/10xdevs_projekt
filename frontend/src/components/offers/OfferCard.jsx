import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';

const OfferCard = ({ offer }) => {
  const [imageError, setImageError] = useState(false);

  // Format date to display
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US');
  };

  // Status badge mapping
  const getStatusBadge = (status) => {
    const statusClasses = {
      active: 'bg-success',
      inactive: 'bg-secondary',
      sold: 'bg-primary',
      moderated: 'bg-danger',
      archived: 'bg-dark'
    };
    
    const statusLabels = {
      active: 'Active',
      inactive: 'Inactive',
      sold: 'Sold',
      moderated: 'Moderated',
      archived: 'Archived'
    };
    
    return (
      <span className={`badge ${statusClasses[status] || 'bg-secondary'} position-absolute top-0 end-0 m-2`}>
        {statusLabels[status] || status}
      </span>
    );
  };

  const handleImageError = () => {
    setImageError(true);
  };

  // Define placeholder image URL
  const placeholderImageUrl = '/assets/placeholder-image.png';

  return (
    <div className="card h-100 shadow-sm">
      <div className="card-img-container position-relative" style={{ height: '180px', overflow: 'hidden' }}>
        {offer.status && getStatusBadge(offer.status)}
        <img
          src={imageError ? placeholderImageUrl : offer.imageUrl}
          className="card-img-top"
          alt={offer.title}
          style={{ objectFit: 'cover', height: '100%', width: '100%' }}
          onError={handleImageError}
        />
      </div>
      <div className="card-body d-flex flex-column">
        <h5 className="card-title text-truncate" title={offer.title}>
          {offer.title}
        </h5>
        
        {offer.description && (
          <p className="card-text small text-truncate mb-2" title={offer.description}>
            {offer.description.substring(0, 150)}{offer.description.length > 150 ? '...' : ''}
          </p>
        )}
        
        <p className="card-text text-primary fw-bold mt-auto mb-1">
          {offer.priceFormatted}
        </p>
        
        <div className="d-flex justify-content-between align-items-center mb-2">
          {offer.quantity > 0 ? (
            <p className="card-text small text-muted mb-0">
              Available: {offer.quantity} pcs.
            </p>
          ) : (
            <p className="card-text small text-danger mb-0">
              Product unavailable
            </p>
          )}
          
          {offer.createdAt && (
            <small className="text-muted">
              {formatDate(offer.createdAt)}
            </small>
          )}
        </div>
        
        <Link 
          to={offer.detailsLink} 
          className="btn btn-outline-primary mt-auto stretched-link"
          aria-label={`View details of offer ${offer.title}`}
        >
          View details
        </Link>
      </div>
    </div>
  );
};

OfferCard.propTypes = {
  offer: PropTypes.shape({
    id: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    description: PropTypes.string,
    priceFormatted: PropTypes.string.isRequired,
    imageUrl: PropTypes.string,
    detailsLink: PropTypes.string.isRequired,
    quantity: PropTypes.number,
    status: PropTypes.string,
    createdAt: PropTypes.string
  }).isRequired
};

export default OfferCard;
