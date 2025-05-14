import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchOfferDetails } from '../../services/offerService';
import { useCart } from '../../contexts/CartContext';
import ImageGallery from '../../components/offers/ImageGallery';
import OfferInfoPanel from '../../components/offers/OfferInfoPanel';
import AddToCartButton from '../../components/cart/AddToCartButton';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const OfferDetailPage = () => {
  // Get offer ID from URL parameters
  const { offerId } = useParams();
  
  // Get cart functions
  const { addToCart } = useCart();
  
  // State management
  const [offer, setOffer] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch offer details on component mount
  useEffect(() => {
    const loadOfferDetails = async () => {
      if (!offerId) {
        setError('Invalid offer ID');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const offerData = await fetchOfferDetails(offerId);
        
        // Map API response to view model
        const mappedOffer = {
          id: offerData.id,
          title: offerData.title,
          description: offerData.description || '',
          price: parseFloat(offerData.price),
          priceFormatted: `${offerData.price} USD`,
          imageUrl: offerData.image_filename 
            ? `/media/offers/${offerData.id}/${offerData.image_filename}` 
            : '/assets/placeholder-image.png',
          quantity: offerData.quantity,
          status: offerData.status,
          statusDisplay: getStatusDisplay(offerData.status),
          statusClassName: getStatusClassName(offerData.status),
          categoryName: offerData.category.name,
          sellerName: getSellerName(offerData.seller),
          sellerId: offerData.seller_id,
          canBeAddedToCart: offerData.status === 'active' && offerData.quantity > 0
        };
        
        setOffer(mappedOffer);
        setError(null);
      } catch (err) {
        console.error('Error fetching offer details:', err);
        if (err.response?.status === 404) {
          setError('Offer with the given ID was not found.');
        } else if (err.response?.status === 403) {
          setError('You do not have permission to view this offer.');
        } else {
          setError('An error occurred while loading the offer. Please try again later.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadOfferDetails();
  }, [offerId]);

  // Helper functions for mapping data
  const getStatusDisplay = (status) => {
    const statusMap = {
      active: 'Active',
      inactive: 'Inactive',
      sold: 'Sold',
      moderated: 'Moderated',
      archived: 'Archived'
    };
    return statusMap[status] || status;
  };

  const getStatusClassName = (status) => {
    const classMap = {
      active: 'bg-success',
      inactive: 'bg-secondary',
      sold: 'bg-primary',
      moderated: 'bg-danger',
      archived: 'bg-dark'
    };
    return classMap[status] || 'bg-secondary';
  };

  const getSellerName = (seller) => {
    if (seller.first_name && seller.last_name) {
      return `${seller.first_name} ${seller.last_name}`;
    }
    return `Seller #${seller.id.substring(0, 8)}`;
  };

  // Handler for adding item to cart
  const handleAddToCart = (id, title) => {
    if (offer) {
      addToCart(id, {
        id: offer.id,
        title: offer.title,
        price: offer.price,
        imageUrl: offer.imageUrl
      });
      
      // Show notification (will be replaced with a toast system later)
      alert(`Added "${title}" to cart`);
    }
  };

  // Render loading state
  if (isLoading) {
    return (
      <div className="container py-5">
        <LoadingSpinner message="Loading offer details..." />
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
      <div className="container py-5">
        <div className="alert alert-danger" role="alert">
          <h4 className="alert-heading">An error occurred!</h4>
          <p>{error}</p>
        </div>
        <Link to="/offers" className="btn btn-primary mt-3">
          Return to offers list
        </Link>
      </div>
    );
  }

  // Render offer details
  return (
    <div className="container py-4">
      <nav aria-label="breadcrumb" className="mb-4">
        <ol className="breadcrumb">
          <li className="breadcrumb-item"><Link to="/">Home</Link></li>
          <li className="breadcrumb-item"><Link to="/offers">Offers</Link></li>
          <li className="breadcrumb-item active" aria-current="page">{offer?.title}</li>
        </ol>
      </nav>

      <div className="row">
        {/* Left column - Image */}
        <div className="col-md-6 mb-4">
          <ImageGallery 
            imageUrl={offer?.imageUrl}
            altText={offer?.title}
          />
        </div>

        {/* Right column - Offer info and actions */}
        <div className="col-md-6">
          <OfferInfoPanel offer={offer} />
          
          {/* Show Add to Cart button if the offer can be added to cart, regardless of authentication */}
          {offer?.canBeAddedToCart && (
            <div className="mt-4">
              <AddToCartButton 
                offerId={offer.id}
                offerTitle={offer.title}
                isDisabled={!offer.canBeAddedToCart}
                onClick={handleAddToCart}
              />
            </div>
          )}
        </div>
      </div>

      <div className="mt-4">
        <Link to="/offers" className="btn btn-outline-secondary">
          &larr; Return to offers list
        </Link>
      </div>
    </div>
  );
};

export default OfferDetailPage; 