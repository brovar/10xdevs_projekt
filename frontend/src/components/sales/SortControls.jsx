import React from 'react';
import PropTypes from 'prop-types';

/**
 * SortControls component for controlling sort order of sales
 * 
 * @param {Object} props - Component props
 * @param {Array} props.options - Array of sorting options
 * @param {string} props.currentSort - Current selected sort value
 * @param {function} props.onSortChange - Handler for sort change events
 * @returns {JSX.Element} - Rendered component
 */
const SortControls = React.memo(({ options, currentSort, onSortChange }) => {
  const handleChange = (e) => {
    onSortChange(e.target.value);
  };
  
  return (
    <div className="mb-4 d-flex align-items-center">
      <label htmlFor="sort-select" className="me-2 text-nowrap">
        Sortuj według:
      </label>
      <select
        id="sort-select"
        className="form-select form-select-sm w-auto"
        value={currentSort}
        onChange={handleChange}
        aria-label="Wybierz sposób sortowania"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
});

SortControls.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired
    })
  ).isRequired,
  currentSort: PropTypes.string.isRequired,
  onSortChange: PropTypes.func.isRequired
};

SortControls.displayName = 'SortControls';

export default SortControls; 