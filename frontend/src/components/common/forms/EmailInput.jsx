import React from 'react';
import PropTypes from 'prop-types';

const EmailInput = ({ name, label, register, errors, rules }) => {
  return (
    <div className="mb-3">
      <label htmlFor={name} className="form-label">
        {label}
      </label>
      <input
        id={name}
        type="email"
        className={`form-control ${errors[name] ? 'is-invalid' : ''}`}
        {...register(name, rules)}
        aria-describedby={`${name}-error`}
      />
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

EmailInput.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  register: PropTypes.func.isRequired,
  errors: PropTypes.object.isRequired,
  rules: PropTypes.object
};

export default React.memo(EmailInput); 