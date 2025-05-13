import React, { useState, useEffect } from 'react';
import { UserRole, UserStatus } from '../../../types/api';
import { UserFiltersState } from '../../../types/viewModels';

interface UserFiltersComponentProps {
  currentFilters: UserFiltersState;
  onFilterChange: (filters: Partial<UserFiltersState>) => void;
}

const UserFiltersComponent: React.FC<UserFiltersComponentProps> = ({
  currentFilters,
  onFilterChange
}) => {
  const [localFilters, setLocalFilters] = useState<UserFiltersState>(currentFilters);

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
      search: undefined,
      role: undefined,
      status: undefined,
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
            <div className="col-12 col-md-4">
              <label htmlFor="search" className="form-label">Wyszukaj</label>
              <input
                type="text"
                className="form-control"
                id="search"
                name="search"
                placeholder="Email, imię lub nazwisko"
                value={localFilters.search || ''}
                onChange={handleInputChange}
              />
            </div>

            {/* Role filter */}
            <div className="col-12 col-md-4">
              <label htmlFor="role" className="form-label">Rola</label>
              <select
                className="form-select"
                id="role"
                name="role"
                value={localFilters.role || ''}
                onChange={handleInputChange}
              >
                <option value="">Wszystkie role</option>
                {Object.values(UserRole).map(role => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>

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
                {Object.values(UserStatus).map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
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

export default UserFiltersComponent; 