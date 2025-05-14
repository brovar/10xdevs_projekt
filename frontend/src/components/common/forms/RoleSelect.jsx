import React from 'react';
import PropTypes from 'prop-types';

const RoleSelect = ({ 
  name, 
  label, 
  register, 
  errors, 
  options, 
  rules = {},
  defaultValue = '' 
}) => {
  return (
    <div className="mb-3">
      <label htmlFor={name} className="form-label">
        {label}
      </label>
      <select
        id={name}
        className={`form-select ${errors[name] ? 'is-invalid' : ''}`}
        defaultValue={defaultValue}
        aria-invalid={errors[name] ? 'true' : 'false'}
        {...register(name, rules)}
      >
        <option value="" disabled>Choose account type</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {errors[name] && (
        <div className="invalid-feedback">
          {errors[name].message}
        </div>
      )}
    </div>
  );
};

RoleSelect.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  register: PropTypes.func.isRequired,
  errors: PropTypes.object.isRequired,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
    })
  ).isRequired,
  rules: PropTypes.object,
  defaultValue: PropTypes.string
};

export default React.memo(RoleSelect); 