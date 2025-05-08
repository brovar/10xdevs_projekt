import React from 'react';
import PropTypes from 'prop-types';

const SubmitButton = ({ label, isLoading, disabled }) => {
  return (
    <div className="d-grid gap-2 mt-4">
      <button
        type="submit"
        className="btn btn-primary"
        disabled={isLoading || disabled}
      >
        {isLoading ? (
          <>
            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            <span>Przetwarzanie...</span>
          </>
        ) : (
          label
        )}
      </button>
    </div>
  );
};

SubmitButton.propTypes = {
  label: PropTypes.string.isRequired,
  isLoading: PropTypes.bool,
  disabled: PropTypes.bool
};

export default React.memo(SubmitButton); 