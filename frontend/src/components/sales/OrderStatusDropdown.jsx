import React, { useCallback } from 'react';
import PropTypes from 'prop-types';
import { Dropdown, Spinner } from 'react-bootstrap';

/**
 * OrderStatusDropdown component for changing order status
 * 
 * @param {Object} props - Component props
 * @param {string} props.orderId - UUID of the order
 * @param {string} props.currentStatus - Current status of the order
 * @param {Array} props.nextStatusOptions - Available status transition options
 * @param {Function} props.onChange - Handler for status change
 * @param {boolean} props.isLoading - Whether the status change is in progress
 * @returns {JSX.Element} - Rendered component
 */
const OrderStatusDropdown = React.memo(({ 
  orderId, 
  currentStatus, 
  nextStatusOptions, 
  onChange, 
  isLoading 
}) => {
  const handleStatusChange = useCallback((newStatus) => {
    onChange(orderId, newStatus);
  }, [orderId, onChange]);

  // If there are no next status options or the dropdown is loading, show an appropriate message
  if (nextStatusOptions.length === 0) {
    return <span className="text-muted">Brak dostępnych akcji</span>;
  }

  return (
    <Dropdown>
      <Dropdown.Toggle 
        variant="outline-primary" 
        size="sm" 
        id={`dropdown-${orderId}`}
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <Spinner animation="border" size="sm" className="me-1" />
            Aktualizacja...
          </>
        ) : (
          'Zmień status'
        )}
      </Dropdown.Toggle>
      
      <Dropdown.Menu>
        {nextStatusOptions.map((option) => (
          <Dropdown.Item 
            key={option.value}
            onClick={() => handleStatusChange(option.value)}
            disabled={isLoading}
          >
            {option.label}
          </Dropdown.Item>
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );
});

OrderStatusDropdown.propTypes = {
  orderId: PropTypes.string.isRequired,
  currentStatus: PropTypes.string.isRequired,
  nextStatusOptions: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired
    })
  ).isRequired,
  onChange: PropTypes.func.isRequired,
  isLoading: PropTypes.bool
};

OrderStatusDropdown.defaultProps = {
  isLoading: false,
  nextStatusOptions: []
};

OrderStatusDropdown.displayName = 'OrderStatusDropdown';

export default OrderStatusDropdown; 