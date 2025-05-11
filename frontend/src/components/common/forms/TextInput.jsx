import React, { useId } from 'react';
import PropTypes from 'prop-types';

/**
 * Reusable component for a single text input field
 * 
 * @param {Object} props - Component props
 * @param {string} props.label - Input label text
 * @param {string} props.name - Input field name
 * @param {string} props.value - Current input value
 * @param {function} props.onChange - Handler for value changes (name, value) => void
 * @param {function} [props.onBlur] - Handler for blur event
 * @param {string} [props.error] - Error message to display
 * @param {boolean} [props.required] - Whether the field is required
 * @param {string} [props.placeholder] - Placeholder text
 * @returns {JSX.Element} - Rendered component
 */
const TextInput = ({
  label,
  name,
  value,
  onChange,
  onBlur,
  error,
  required = false,
  placeholder = ''
}) => {
  const id = useId();
  const inputId = `${id}-${name}`;
  const errorId = `${inputId}-error`;
  
  const handleChange = (e) => {
    onChange(name, e.target.value);
  };
  
  return (
    <div className="mb-3">
      <label htmlFor={inputId} className="form-label">
        {label}
        {required && <span className="text-danger ms-1">*</span>}
      </label>
      <input
        type="text"
        className={`form-control ${error ? 'is-invalid' : ''}`}
        id={inputId}
        name={name}
        value={value}
        onChange={handleChange}
        onBlur={onBlur}
        placeholder={placeholder}
        aria-describedby={error ? errorId : undefined}
        aria-invalid={error ? 'true' : 'false'}
        required={required}
      />
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

TextInput.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  onBlur: PropTypes.func,
  error: PropTypes.string,
  required: PropTypes.bool,
  placeholder: PropTypes.string
};

export default React.memo(TextInput); 