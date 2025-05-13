import React from 'react';
import PropTypes from 'prop-types';
import OfferCard from './OfferCard';

const OfferList = ({ offers = [], isLoading = false }) => {
  // If there are no offers and not loading, show a message
  if (offers.length === 0 && !isLoading) {
    return (
      <div className="row">
        <div className="col-12 text-center py-5">
          <h3>Brak ofert spełniających wybrane kryteria.</h3>
          <p className="text-muted">Spróbuj zmienić kryteria wyszukiwania lub filtry.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 row-cols-xl-4 g-4">
      {offers.map((offer) => (
        <div className="col" key={offer.id}>
          <OfferCard offer={offer} />
        </div>
      ))}
    </div>
  );
};

OfferList.propTypes = {
  offers: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      description: PropTypes.string,
      priceFormatted: PropTypes.string.isRequired,
      imageUrl: PropTypes.string,
      detailsLink: PropTypes.string.isRequired,
      quantity: PropTypes.number,
      status: PropTypes.string,
      createdAt: PropTypes.string,
      categoryId: PropTypes.number,
      sellerId: PropTypes.string
    })
  ),
  isLoading: PropTypes.bool
};

export default OfferList;
