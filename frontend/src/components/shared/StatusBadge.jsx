import React from 'react';
import PropTypes from 'prop-types';

/**
 * StatusBadge component for displaying order status with appropriate styling
 * @param {Object} props - Component props
 * @param {string} props.text - Text to display in the badge
 * @param {string} props.className - CSS class for styling the badge
 * @returns {JSX.Element} - Rendered component
 */
const StatusBadge = React.memo(({ text, className }) => {
  return (
    <span 
      className={`badge ${className}`}
      aria-label={`Status: ${text}`}
    >
      {text}
    </span>
  );
});

StatusBadge.propTypes = {
  text: PropTypes.string.isRequired,
  className: PropTypes.string
};

StatusBadge.defaultProps = {
  className: 'bg-secondary'
};

StatusBadge.displayName = 'StatusBadge';

export default StatusBadge; 