import React, { useCallback } from 'react';
import PropTypes from 'prop-types';

const SearchFilters = ({ 
  categories = [], 
  selectedCategoryId = null, 
  onCategoryChange, 
  sortBy = 'created_at_desc',
  onSortChange,
  isLoading = false 
}) => {
  const handleCategoryChange = useCallback((e) => {
    const value = e.target.value;
    onCategoryChange(value ? parseInt(value, 10) : null);
  }, [onCategoryChange]);

  const handleSortChange = useCallback((e) => {
    onSortChange(e.target.value);
  }, [onSortChange]);

  return (
    <div>
      <div className="mb-3">
        <label htmlFor="categoryFilter" className="form-label">
          Filter by category:
        </label>
        <select
          id="categoryFilter"
          className="form-select"
          value={selectedCategoryId || ''}
          onChange={handleCategoryChange}
          disabled={isLoading || categories.length === 0}
          aria-label="Filter by category"
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
        {isLoading && (
          <div className="text-muted small mt-1">Loading categories...</div>
        )}
      </div>

      <div className="mb-3">
        <label htmlFor="sortOrder" className="form-label">
          Sort by:
        </label>
        <select
          id="sortOrder"
          className="form-select"
          value={sortBy}
          onChange={handleSortChange}
          aria-label="Sort by"
        >
          <option value="created_at_desc">Newest</option>
          <option value="price_asc">Price: Low to High</option>
          <option value="price_desc">Price: High to Low</option>
          <option value="relevance">Relevance</option>
        </select>
      </div>
    </div>
  );
};

SearchFilters.propTypes = {
  categories: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired
    })
  ),
  selectedCategoryId: PropTypes.number,
  onCategoryChange: PropTypes.func.isRequired,
  sortBy: PropTypes.string,
  onSortChange: PropTypes.func.isRequired,
  isLoading: PropTypes.bool
};

export default SearchFilters;
