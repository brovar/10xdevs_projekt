import React, { useState, useEffect } from 'react';
import { OrderStatus } from '../../../types/api';
import { OrderFiltersState } from '../../../types/viewModels';

interface OrderFiltersComponentProps {
  currentFilters: OrderFiltersState;
  onFilterChange: (filters: Partial<OrderFiltersState>) => void;
}

const OrderFiltersComponent: React.FC<OrderFiltersComponentProps> = ({
  currentFilters,
  onFilterChange
}) => {
  const [localFilters, setLocalFilters] = useState<OrderFiltersState>(currentFilters);

  // Update local state when props change
  useEffect(() => {
    setLocalFilters(currentFilters);
  }, [currentFilters]);

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setLocalFilters(prev => ({
      ...prev,
      [name]: value || undefined // Convert empty string to undefined
    }));
  };

  // Apply filters
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange(localFilters);
  };

  // Reset filters
  const handleReset = () => {
    const resetFilters = {
      status: undefined,
      buyer_id: undefined,
      seller_id: undefined,
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
            {/* Status filter */}
            <div className="col-12 col-md-4">
              <label htmlFor="status" className="form-label">Status</label>
              <select
                className="form-select"
                id="status"
                name="status"
                value={localFilters.status || ''}
                onChange={handleInputChange}
              >
                <option value="">Wszystkie statusy</option>
                {Object.values(OrderStatus).map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>

            {/* Buyer ID filter */}
            <div className="col-12 col-md-4">
              <label htmlFor="buyer_id" className="form-label">ID Kupującego</label>
              <input
                type="text"
                className="form-control"
                id="buyer_id"
                name="buyer_id"
                placeholder="ID kupującego"
                value={localFilters.buyer_id || ''}
                onChange={handleInputChange}
              />
            </div>

            {/* Seller ID filter */}
            <div className="col-12 col-md-4">
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

export default OrderFiltersComponent; 