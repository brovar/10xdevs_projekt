import React, { useState, useEffect } from 'react';
import { OfferStatus } from '../../../types/api';
import { OfferFiltersState } from '../../../types/viewModels';

interface OfferFiltersComponentProps {
  currentFilters: OfferFiltersState;
  onFilterChange: (filters: Partial<OfferFiltersState>) => void;
}

const OfferFiltersComponent: React.FC<OfferFiltersComponentProps> = ({
  currentFilters,
  onFilterChange
}) => {
  const [localFilters, setLocalFilters] = useState<OfferFiltersState>(currentFilters);

  // Update local state when props change
  useEffect(() => {
    setLocalFilters(currentFilters);
  }, [currentFilters]);

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    // Handle numeric values
    if (name === 'category_id') {
      setLocalFilters(prev => ({
        ...prev,
        [name]: value ? parseInt(value, 10) : undefined
      }));
    } else {
      setLocalFilters(prev => ({
        ...prev,
        [name]: value || undefined // Convert empty string to undefined
      }));
    }
  };

  // Apply filters
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange(localFilters);
  };

  // Reset filters
  const handleReset = () => {
    const resetFilters = {
      search: undefined,
      category_id: undefined,
      seller_id: undefined,
      status: undefined,
      sort: currentFilters.sort || 'created_at_desc',
      page: 1,
      limit: currentFilters.limit
    };
    setLocalFilters(resetFilters);
    onFilterChange(resetFilters);
  };

  return (
    <div className="card mb-4">
      <div className="card-body">
        <h5 className="card-title">Filtry</h5>
        <form onSubmit={handleSubmit}>
          <div className="row g-3">
            {/* Search input */}
            <div className="col-12 col-md-6">
              <label htmlFor="search" className="form-label">Wyszukaj</label>
              <input
                type="text"
                className="form-control"
                id="search"
                name="search"
                placeholder="Tytuł lub opis"
                value={localFilters.search || ''}
                onChange={handleInputChange}
              />
            </div>

            {/* Category filter */}
            <div className="col-12 col-md-6">
              <label htmlFor="category_id" className="form-label">Kategoria ID</label>
              <input
                type="number"
                className="form-control"
                id="category_id"
                name="category_id"
                placeholder="ID kategorii"
                value={localFilters.category_id || ''}
                onChange={handleInputChange}
                min="1"
              />
            </div>

            {/* Seller ID filter */}
            <div className="col-12 col-md-6">
              <label htmlFor="seller_id" className="form-label">ID Sprzedawcy</label>
              <input
                type="text"
                className="form-control"
                id="seller_id"
                name="seller_id"
                placeholder="ID sprzedawcy"
                value={localFilters.seller_id || ''}
                onChange={handleInputChange}
              />
            </div>

            {/* Status filter */}
            <div className="col-12 col-md-6">
              <label htmlFor="status" className="form-label">Status</label>
              <select
                className="form-select"
                id="status"
                name="status"
                value={localFilters.status || ''}
                onChange={handleInputChange}
              >
                <option value="">Wszystkie statusy</option>
                {Object.values(OfferStatus).map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>

            {/* Sort filter */}
            <div className="col-12 col-md-6">
              <label htmlFor="sort" className="form-label">Sortowanie</label>
              <select
                className="form-select"
                id="sort"
                name="sort"
                value={localFilters.sort || 'created_at_desc'}
                onChange={handleInputChange}
              >
                <option value="created_at_desc">Najnowsze</option>
                <option value="price_asc">Cena: rosnąco</option>
                <option value="price_desc">Cena: malejąco</option>
                <option value="relevance">Trafność</option>
              </select>
            </div>

            {/* Action buttons */}
            <div className="col-12 d-flex justify-content-end mt-3">
              <button
                type="button"
                className="btn btn-outline-secondary me-2"
                onClick={handleReset}
              >
                Resetuj
              </button>
              <button type="submit" className="btn btn-primary">
                Zastosuj filtry
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default OfferFiltersComponent; 