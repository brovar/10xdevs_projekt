import React, { useId } from 'react';
import PropTypes from 'prop-types';

/**
 * Reusable component for a dropdown select input field
 * 
 * @param {Object} props - Component props
 * @param {string} props.label - Input label text
 * @param {string} props.name - Input field name
 * @param {string} props.value - Current selected value
 * @param {Array} props.options - Array of options objects with value and label
 * @param {function} props.onChange - Handler for value changes (name, value) => void
 * @param {function} [props.onBlur] - Handler for blur event
 * @param {string} [props.error] - Error message to display
 * @param {boolean} [props.required] - Whether the field is required
 * @param {string} [props.placeholder] - Placeholder text for empty selection
 * @returns {JSX.Element} - Rendered component
 */
const SelectInput = ({
  label,
  name,
  value,
  options,
  onChange,
  onBlur,
  error,
  required = false,
  placeholder = 'Wybierz...'
}) => {
  const id = useId();
  const selectId = `${id}-${name}`;
  const errorId = `${selectId}-error`;
  
  const handleChange = (e) => {
    onChange(name, e.target.value);
  };
  
  return (
    <div className="mb-3">
      <label htmlFor={selectId} className="form-label">
        {label}
        {required && <span className="text-danger ms-1">*</span>}
      </label>
      <select
        className={`form-select ${error ? 'is-invalid' : ''}`}
        id={selectId}
        name={name}
        value={value}
        onChange={handleChange}
        onBlur={onBlur}
        aria-describedby={error ? errorId : undefined}
        aria-invalid={error ? 'true' : 'false'}
        required={required}
      >
        <option value="" disabled>{placeholder}</option>
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <div 
          id={errorId} 
          className="invalid-feedback"
          aria-live="polite"
        >
          {error}
        </div>
      )}
    </div>
  );
};

SelectInput.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired
    })
  ).isRequired,
  onChange: PropTypes.func.isRequired,
  onBlur: PropTypes.func,
  error: PropTypes.string,
  required: PropTypes.bool,
  placeholder: PropTypes.string
};

export default React.memo(SelectInput); 