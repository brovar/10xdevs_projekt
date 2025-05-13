import React from 'react';

const OfferCardSkeleton = () => {
  return (
    <div className="card h-100 shadow-sm">
      <div className="placeholder-glow">
        {/* Image placeholder */}
        <div className="card-img-top bg-light" style={{ height: '180px' }}></div>
        
        <div className="card-body d-flex flex-column">
          {/* Title placeholder */}
          <h5 className="card-title mb-2">
            <span className="placeholder col-9"></span>
          </h5>
          
          {/* Price placeholder */}
          <p className="card-text mt-auto mb-1">
            <span className="placeholder col-4"></span>
          </p>
          
          {/* Quantity placeholder */}
          <p className="card-text small mb-3">
            <span className="placeholder col-6"></span>
          </p>
          
          {/* Button placeholder */}
          <div className="mt-auto">
            <span className="placeholder col-12 placeholder-lg bg-primary"></span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OfferCardSkeleton;
