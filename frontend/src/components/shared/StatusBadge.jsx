import React from 'react';
import PropTypes from 'prop-types';
import { Badge } from 'react-bootstrap';

/**
 * Map of order statuses to display text and style classes
 */
export const orderStatusMap = {
  pending_payment: { text: 'Oczekuje na płatność', variant: 'warning' },
  processing: { text: 'Przetwarzane', variant: 'info' },
  shipped: { text: 'Wysłane', variant: 'primary' },
  delivered: { text: 'Dostarczone', variant: 'success' },
  cancelled: { text: 'Anulowane', variant: 'danger' },
  failed: { text: 'Nieudane', variant: 'secondary' },
  // For the existing OrdersPage mock data
  completed: { text: 'Zrealizowane', variant: 'success' },
  pending: { text: 'Oczekujące', variant: 'warning' },
};

/**
 * StatusBadge component displays a status with appropriate styling
 * 
 * @param {Object} props
 * @param {string} props.status - Status key (from backend)
 * @param {string} [props.className] - Additional CSS classes
 */
const StatusBadge = ({ status, className = '' }) => {
  const statusConfig = orderStatusMap[status] || { 
    text: status, 
    variant: 'secondary'
  };

  return (
    <Badge 
      bg={statusConfig.variant} 
      className={className}
      aria-label={`Status: ${statusConfig.text}`}
    >
      {statusConfig.text}
    </Badge>
  );
};

StatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
  className: PropTypes.string
};

export default StatusBadge; 