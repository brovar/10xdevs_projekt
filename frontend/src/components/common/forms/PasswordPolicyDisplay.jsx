import React, { useMemo } from 'react';
import PropTypes from 'prop-types';

const PasswordPolicyDisplay = ({ passwordValue }) => {
  const policyChecks = useMemo(() => [
    {
      id: 'length',
      label: 'Co najmniej 10 znaków',
      check: (password) => password.length >= 10
    },
    {
      id: 'uppercase',
      label: 'Co najmniej jedna wielka litera',
      check: (password) => /[A-Z]/.test(password)
    },
    {
      id: 'lowercase',
      label: 'Co najmniej jedna mała litera',
      check: (password) => /[a-z]/.test(password)
    },
    {
      id: 'digit-special',
      label: 'Co najmniej jedna cyfra lub znak specjalny',
      check: (password) => /[0-9!@#$%^&*(),.?":{}|<>]/.test(password)
    }
  ], []);

  return (
    <div className="password-policy card p-2">
      <small className="text-muted mb-2">Wymagania hasła:</small>
      <ul className="list-unstyled mb-0">
        {policyChecks.map((item) => {
          const isMet = item.check(passwordValue);
          return (
            <li 
              key={item.id} 
              className={isMet ? 'text-success' : 'text-muted'}
              aria-live="polite"
            >
              <small>
                <i 
                  className={`bi ${isMet ? 'bi-check-circle-fill' : 'bi-circle'}`} 
                  aria-hidden="true"
                ></i>
                {' '}
                {item.label}
              </small>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

PasswordPolicyDisplay.propTypes = {
  passwordValue: PropTypes.string.isRequired
};

export default React.memo(PasswordPolicyDisplay); 