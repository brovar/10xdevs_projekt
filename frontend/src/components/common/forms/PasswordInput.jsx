import React from 'react';
import PropTypes from 'prop-types';
import PasswordPolicyDisplay from './PasswordPolicyDisplay';

const PasswordInput = ({ 
  name, 
  label, 
  register, 
  errors, 
  rules, 
  watch, 
  showPolicy = false 
}) => {
  const passwordValue = watch ? watch(name, '') : '';
  
  return (
    <div className="mb-3 position-relative">
      <label htmlFor={name} className="form-label">
        {label}
      </label>
      <div className="row">
        <div className={showPolicy ? "col-md-7" : "col-12"}>
          <input
            id={name}
            type="password"
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
        {showPolicy && (
          <div className="col-md-5">
            <PasswordPolicyDisplay passwordValue={passwordValue} />
          </div>
        )}
      </div>
    </div>
  );
};

PasswordInput.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  register: PropTypes.func.isRequired,
  errors: PropTypes.object.isRequired,
  rules: PropTypes.object,
  watch: PropTypes.func,
  showPolicy: PropTypes.bool
};

export default React.memo(PasswordInput); 