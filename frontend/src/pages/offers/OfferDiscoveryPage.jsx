import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchOffers, fetchCategories } from '../../services/offerService';
import SearchBar from '../../components/offers/SearchBar';
import SearchFilters from '../../components/offers/SearchFilters';
import OfferList from '../../components/offers/OfferList';
import Pagination from '../../components/common/Pagination';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import OfferCardSkeleton from '../../components/offers/OfferCardSkeleton';

const OfferDiscoveryPage = () => {
  // State management
  const [searchParams, setSearchParams] = useSearchParams();
  const [offers, setOffers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [paginationData, setPaginationData] = useState(null);
  const [isLoadingOffers, setIsLoadingOffers] = useState(true);
  const [isLoadingCategories, setIsLoadingCategories] = useState(true);
  const [error, setError] = useState(null);

  // Parse query parameters
  const currentPage = parseInt(searchParams.get('page') || '1', 10);
  const searchTerm = searchParams.get('search') || '';
  const categoryId = searchParams.get('category_id') ? parseInt(searchParams.get('category_id'), 10) : null;
  const sortBy = searchParams.get('sort') || 'created_at_desc';

  // Fetch categories on component mount
  useEffect(() => {
    const loadCategories = async () => {
      try {
        setIsLoadingCategories(true);
        const response = await fetchCategories();
        setCategories(response.items.map(category => ({
          id: category.id,
          name: category.name
        })));
        setError(null);
      } catch (err) {
        console.error('Error fetching categories:', err);
        setError('Nie udało się załadować kategorii.');
      } finally {
        setIsLoadingCategories(false);
      }
    };

    loadCategories();
  }, []);

  // Fetch offers whenever search parameters change
  useEffect(() => {
    const loadOffers = async () => {
      try {
        setIsLoadingOffers(true);
        
        const params = {
          page: currentPage,
          limit: 20,
          sort: sortBy
        };
        
        if (searchTerm) params.search = searchTerm;
        if (categoryId) params.category_id = categoryId;
        
        const response = await fetchOffers(params);
        
        setOffers(response.items.map(offer => ({
          id: offer.id,
          title: offer.title,
          description: offer.description || '',
          priceFormatted: `${offer.price} USD`,
          imageUrl: offer.image_filename 
            ? `/media/offers/${offer.id}/${offer.image_filename}` 
            : '/assets/placeholder-image.png',
          detailsLink: `/offers/${offer.id}`,
          categoryId: offer.category_id,
          quantity: offer.quantity,
          status: offer.status,
          sellerId: offer.seller_id,
          createdAt: offer.created_at
        })));
        
        setPaginationData({
          currentPage: response.page,
          totalPages: response.pages,
          totalItems: response.total
        });
        
        setError(null);
      } catch (err) {
        console.error('Error fetching offers:', err);
        setError('Nie udało się załadować ofert. Spróbuj ponownie później.');
        setOffers([]);
        setPaginationData(null);
      } finally {
        setIsLoadingOffers(false);
      }
    };

    loadOffers();
  }, [currentPage, searchTerm, categoryId, sortBy]);

  // Handler for search form submission
  const handleSearch = useCallback((term) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('search', term);
    newParams.set('page', '1'); // Reset to first page on new search
    setSearchParams(newParams);
  }, [searchParams, setSearchParams]);

  // Handler for category change
  const handleCategoryChange = useCallback((categoryId) => {
    const newParams = new URLSearchParams(searchParams);
    if (categoryId) {
      newParams.set('category_id', categoryId.toString());
    } else {
      newParams.delete('category_id');
    }
    newParams.set('page', '1'); // Reset to first page on category change
    setSearchParams(newParams);
  }, [searchParams, setSearchParams]);

  // Handler for sort change
  const handleSortChange = useCallback((sort) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('sort', sort);
    newParams.set('page', '1'); // Reset to first page on sort change
    setSearchParams(newParams);
  }, [searchParams, setSearchParams]);

  // Handler for page change
  const handlePageChange = useCallback((page) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', page.toString());
    setSearchParams(newParams);
  }, [searchParams, setSearchParams]);

  // Handler for retrying after error
  const handleRetry = useCallback(() => {
    window.location.reload();
  }, []);

  // Determine page title/header based on search/filter params
  const pageTitle = searchTerm 
    ? `Wyniki wyszukiwania dla: "${searchTerm}"` 
    : categoryId 
      ? `Kategoria: ${categories.find(c => c.id === categoryId)?.name || 'Ładowanie...'}`
      : 'Witaj w Steambay!';

  // Determine if we should show skeletons
  const showSkeletons = isLoadingOffers && offers.length === 0;

  return (
    <div className="container my-4">
      <div className="row mb-4">
        <div className="col-12">
          <h1>{pageTitle}</h1>
          {searchTerm && (
            <p className="text-muted">
              {paginationData ? (
                `Znaleziono ${paginationData.totalItems} wyników`
              ) : isLoadingOffers ? (
                'Wyszukiwanie...'
              ) : (
                'Brak wyników'
              )}
            </p>
          )}
        </div>
      </div>

      <div className="row mb-4">
        <div className="col-md-8">
          <SearchBar 
            initialSearchTerm={searchTerm} 
            onSearch={handleSearch} 
            placeholder="Wyszukaj produkty..."
          />
        </div>
        <div className="col-md-4">
          <SearchFilters 
            categories={categories} 
            selectedCategoryId={categoryId}
            onCategoryChange={handleCategoryChange}
            sortBy={sortBy}
            onSortChange={handleSortChange}
            isLoading={isLoadingCategories}
          />
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          <div className="d-flex justify-content-between align-items-center">
            <div>{error}</div>
            <button 
              className="btn btn-outline-danger"
              onClick={handleRetry}
              aria-label="Odśwież stronę"
            >
              Odśwież
            </button>
          </div>
        </div>
      )}

      {showSkeletons ? (
        <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 row-cols-xl-4 g-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <div className="col" key={index}>
              <OfferCardSkeleton />
            </div>
          ))}
        </div>
      ) : isLoadingOffers ? (
        <div className="d-flex justify-content-center my-5">
          <LoadingSpinner message="Aktualizowanie ofert..." />
        </div>
      ) : (
        <>
          <OfferList offers={offers} isLoading={isLoadingOffers} />
          
          {paginationData && paginationData.totalPages > 1 && (
            <div className="row mt-4">
              <div className="col-12 d-flex justify-content-center">
                <Pagination 
                  currentPage={paginationData.currentPage} 
                  totalPages={paginationData.totalPages} 
                  onPageChange={handlePageChange}
                />
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default OfferDiscoveryPage; 