import React, { useState, useCallback } from 'react';
import useAdminData from '../../../hooks/useAdminData.ts';
import { adminOffersApi } from '../../../services/adminService.ts';
import { OfferFiltersState, PaginationData, ConfirmActionState } from '../../../types/viewModels.ts';
import { OfferSummaryDTO, OfferListResponse, AdminOfferListQueryParams, OfferStatus } from '../../../types/api.ts';

import OfferFiltersComponent from './OfferFiltersComponent.tsx';
import AdminOfferListTable from './AdminOfferListTable.tsx';
import PaginationComponent from '../../shared/PaginationComponent.tsx';
import ConfirmationModal from '../../shared/ConfirmationModal.tsx';
import LoadingSpinner from '../../shared/LoadingSpinner.tsx';
import ErrorMessageDisplay from '../../shared/ErrorMessageDisplay.tsx';

const OffersManagementTab: React.FC = () => {
  // Modal state for confirmation actions
  const [confirmAction, setConfirmAction] = useState<ConfirmActionState | null>(null);
  
  // Default filters
  const initialFilters: OfferFiltersState = {
    page: 1,
    limit: 10,
    sort: 'created_at_desc'
  };

  // Convert UI filter state to API query params
  const convertFiltersToQueryParams = useCallback(
    (filters: OfferFiltersState): AdminOfferListQueryParams => {
      const queryParams: AdminOfferListQueryParams = {
        page: filters.page,
        limit: filters.limit,
        sort: filters.sort
      };

      if (filters.search) {
        queryParams.search = filters.search;
      }

      if (filters.category_id) {
        queryParams.category_id = filters.category_id;
      }

      if (filters.seller_id) {
        queryParams.seller_id = filters.seller_id;
      }

      if (filters.status) {
        // Type assertion since we know it's a valid OfferStatus from the UI
        queryParams.status = filters.status as OfferStatus;
      }

      return queryParams;
    },
    []
  );

  // Extract items and pagination data from API response
  const extractItems = useCallback((response: OfferListResponse): OfferSummaryDTO[] => {
    return response.items;
  }, []);

  const extractPaginationData = useCallback((response: OfferListResponse): PaginationData => {
    return {
      currentPage: response.page,
      totalPages: response.pages,
      totalItems: response.total,
      limit: response.limit
    };
  }, []);

  // Use admin data hook for fetching offers with the conversion function
  const { 
    items: offers, 
    isLoading, 
    error, 
    paginationData, 
    queryParams,
    handlePageChange,
    handleFiltersChange,
    fetchData
  } = useAdminData<OfferFiltersState, OfferListResponse, OfferSummaryDTO>({
    fetchFunction: (filters) => adminOffersApi.getOffers(convertFiltersToQueryParams(filters)),
    initialParams: initialFilters,
    extractItems,
    extractPaginationData
  });

  // Handler for moderating an offer
  const handleModerateOffer = useCallback((offerId: string) => {
    // Find offer info for the confirmation message
    const offerToModerate = offers.find(offer => offer.id === offerId);
    if (!offerToModerate) return;

    setConfirmAction({
      type: 'moderate_offer',
      id: offerId,
      additionalInfo: `Czy na pewno chcesz moderować ofertę "${offerToModerate.title}"?`
    });
  }, [offers]);

  // Handler for unmoderating an offer
  const handleUnmoderateOffer = useCallback((offerId: string) => {
    // Find offer info for the confirmation message
    const offerToUnmoderate = offers.find(offer => offer.id === offerId);
    if (!offerToUnmoderate) return;

    setConfirmAction({
      type: 'unmoderate_offer',
      id: offerId,
      additionalInfo: `Czy na pewno chcesz odmoderować ofertę "${offerToUnmoderate.title}"?`
    });
  }, [offers]);

  // Handle confirmation for moderate/unmoderate actions
  const handleConfirmAction = useCallback(async () => {
    if (!confirmAction) return;

    try {
      if (confirmAction.type === 'moderate_offer') {
        await adminOffersApi.moderateOffer(confirmAction.id);
      } else if (confirmAction.type === 'unmoderate_offer') {
        await adminOffersApi.unmoderateOffer(confirmAction.id);
      }
      // Refresh the data after action is completed
      fetchData();
    } catch (err) {
      console.error('Action failed:', err);
      // Error handling could be improved with a toast notification
    } finally {
      // Close the confirmation modal
      setConfirmAction(null);
    }
  }, [confirmAction, fetchData]);

  // Close confirmation modal
  const handleCancelAction = () => {
    setConfirmAction(null);
  };

  return (
    <div className="offers-management-tab">
      <h2 className="mb-4">Zarządzanie Ofertami</h2>
      
      {/* Filters */}
      <OfferFiltersComponent 
        currentFilters={queryParams}
        onFilterChange={handleFiltersChange}
      />
      
      {/* Loading state */}
      {isLoading && <LoadingSpinner text="Ładowanie ofert..." />}
      
      {/* Error state */}
      {error && !isLoading && (
        <ErrorMessageDisplay error={error} className="mb-4" />
      )}
      
      {/* Offers table */}
      {!isLoading && !error && (
        <>
          <AdminOfferListTable 
            offers={offers} 
            onModerate={handleModerateOffer}
            onUnmoderate={handleUnmoderateOffer}
          />
          
          {/* Pagination */}
          {paginationData && (
            <div className="mt-4">
              <PaginationComponent 
                paginationInfo={paginationData}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </>
      )}
      
      {/* Confirmation Modal */}
      {confirmAction && (
        <ConfirmationModal
          isOpen={true}
          title={confirmAction.type === 'moderate_offer' ? 'Moderowanie oferty' : 'Odmoderowanie oferty'}
          message={confirmAction.additionalInfo || ''}
          onConfirm={handleConfirmAction}
          onCancel={handleCancelAction}
          confirmButtonText={confirmAction.type === 'moderate_offer' ? 'Moderuj' : 'Odmoderuj'}
          variant={confirmAction.type === 'moderate_offer' ? 'primary' : 'warning'}
        />
      )}
    </div>
  );
};

export default OffersManagementTab; 