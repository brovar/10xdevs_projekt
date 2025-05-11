import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import OfferForm from '../../components/offers/OfferForm';

/**
 * Page component for creating new offers
 * @returns {JSX.Element} - Rendered component
 */
const CreateOfferPage = () => {
  const navigate = useNavigate();
  
  // Handle successful form submission
  const handleSuccess = useCallback((newOffer) => {
    // Show success message (could use a notification system)
    // Redirect to seller's offers list
    navigate('/seller/offers', { 
      state: { 
        notification: {
          type: 'success',
          message: 'Oferta została pomyślnie utworzona'
        }
      }
    });
  }, [navigate]);
  
  // Handle form cancellation
  const handleCancel = useCallback(() => {
    navigate('/seller/offers');
  }, [navigate]);
  
  return (
    <div className="container py-4">
      <div className="row">
        <div className="col-12">
          <h1 className="mb-4">Dodaj nową ofertę</h1>
          
          <div className="card shadow-sm">
            <div className="card-body p-4">
              <OfferForm 
                onSuccess={handleSuccess} 
                onCancel={handleCancel} 
              />
            </div>
          </div>
          
          <div className="mt-4">
            <small className="text-muted">
              * Pola oznaczone gwiazdką są wymagane
            </small>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreateOfferPage;
