import React, { useId } from 'react';
import PropTypes from 'prop-types';

/**
 * Reusable component for a numeric input field with decimal support
 * 
 * @param {Object} props - Component props
 * @param {string} props.label - Input label text
 * @param {string} props.name - Input field name
 * @param {string} props.value - Current input value as string
 * @param {function} props.onChange - Handler for value changes (name, value) => void
 * @param {function} [props.onBlur] - Handler for blur event
 * @param {string} [props.error] - Error message to display
 * @param {boolean} [props.required] - Whether the field is required
 * @param {number} [props.min] - Minimum allowed value
 * @param {string} [props.step] - Step value for increments/decrements
 * @param {boolean} [props.isDecimal] - Whether to allow decimal values
 * @param {string} [props.placeholder] - Placeholder text
 * @returns {JSX.Element} - Rendered component
 */
const NumberInput = ({
  label,
  name,
  value,
  onChange,
  onBlur,
  error,
  required = false,
  min = undefined,
  step = undefined,
  isDecimal = false,
  placeholder = ''
}) => {
  const id = useId();
  const inputId = `${id}-${name}`;
  const errorId = `${inputId}-error`;
  
  // Default step based on decimal/integer mode
  const defaultStep = isDecimal ? '0.01' : '1';
  const actualStep = step || defaultStep;
  
  const handleChange = (e) => {
    let newValue = e.target.value;
    
    // For empty input or minus sign only, allow it as is
    if (newValue === '' || newValue === '-') {
      onChange(name, newValue);
      return;
    }
    
    // Check if the value matches our expected number format
    const numberRegex = isDecimal 
      ? /^-?\d*\.?\d*$/ // Allow decimal numbers
      : /^-?\d*$/;      // Allow only integers
      
    if (numberRegex.test(newValue)) {
      onChange(name, newValue);
    }
  };
  
  return (
    <div className="mb-3">
      <label htmlFor={inputId} className="form-label">
        {label}
        {required && <span className="text-danger ms-1">*</span>}
      </label>
      <input
        type="text" 
        inputMode={isDecimal ? "decimal" : "numeric"}
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
        min={min}
        step={actualStep}
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

NumberInput.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  onBlur: PropTypes.func,
  error: PropTypes.string,
  required: PropTypes.bool,
  min: PropTypes.number,
  step: PropTypes.string,
  isDecimal: PropTypes.bool,
  placeholder: PropTypes.string
};

export default React.memo(NumberInput); 