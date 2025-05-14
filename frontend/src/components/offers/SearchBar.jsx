import React, { useState, useCallback } from 'react';
import PropTypes from 'prop-types';

const SearchBar = ({ initialSearchTerm = '', onSearch, placeholder = 'Search...' }) => {
  const [searchTerm, setSearchTerm] = useState(initialSearchTerm);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    onSearch(searchTerm);
  }, [searchTerm, onSearch]);

  const handleChange = useCallback((e) => {
    setSearchTerm(e.target.value);
  }, []);

  return (
    <form className="d-flex" onSubmit={handleSubmit} role="search">
      <div className="input-group">
        <input
          type="search"
          className="form-control"
          placeholder={placeholder}
          aria-label={placeholder}
          value={searchTerm}
          onChange={handleChange}
        />
        <button className="btn btn-primary" type="submit" aria-label="Search">
          <i className="bi bi-search me-1"></i> Search
        </button>
      </div>
    </form>
  );
};

SearchBar.propTypes = {
  initialSearchTerm: PropTypes.string,
  onSearch: PropTypes.func.isRequired,
  placeholder: PropTypes.string
};

export default SearchBar; 