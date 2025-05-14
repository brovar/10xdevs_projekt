import React, { useState } from 'react';
import PropTypes from 'prop-types';

const ImageGallery = ({ imageUrl, altText }) => {
  const [imageError, setImageError] = useState(false);
  const placeholderImage = '/assets/placeholder-image.png';
  
  const handleImageError = () => {
    setImageError(true);
  };

  const displayImage = imageError || !imageUrl ? placeholderImage : imageUrl;

  return (
    <div className="card shadow-sm">
      <div className="card-body p-0">
        <div className="position-relative" style={{ minHeight: '300px' }}>
          <img
            src={displayImage}
            alt={altText || 'Zdjęcie produktu'}
            className="img-fluid rounded"
            style={{ 
              width: '100%', 
              height: '100%', 
              objectFit: 'contain',
              maxHeight: '500px'
            }}
            onError={handleImageError}
          />
          {(imageError || !imageUrl) && (
            <div className="position-absolute top-50 start-50 translate-middle text-muted">
              <div className="text-center">
                <i className="bi bi-image fs-1 mb-2"></i>
                <p>No image</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

ImageGallery.propTypes = {
  imageUrl: PropTypes.string,
  altText: PropTypes.string
};

export default ImageGallery; 