import React from 'react';
import PropTypes from 'prop-types';

const RoleSelect = ({ name, label, register, errors, options, rules }) => {
  return (
    <div className="mb-3">
      <label htmlFor={name} className="form-label">
        {label}
      </label>
      <select
        id={name}
        className={`form-select ${errors[name] ? 'is-invalid' : ''}`}
        {...register(name, rules)}
        aria-describedby={`${name}-error`}
      >
        <option value="">Wybierz typ konta</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {errors[name] && (
        <div 
          className="invalid-feedback" 
          id={`${name}-error`}
        >
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
      label: PropTypes.string.isRequired
    })
  ).isRequired,
  rules: PropTypes.object
};

export default React.memo(RoleSelect); 