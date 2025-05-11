import React from 'react';
import PropTypes from 'prop-types';
import StatusBadge from '../shared/StatusBadge';
import OrderStatusDropdown from './OrderStatusDropdown';

/**
 * SaleItem component for displaying a single sale row in the table
 * 
 * @param {Object} props - Component props
 * @param {Object} props.sale - Sale item view model
 * @param {Function} props.onStatusChange - Handler for status change
 * @param {boolean} props.isUpdatingStatus - Whether this item's status is being updated
 * @returns {JSX.Element} - Rendered component
 */
const SaleItem = React.memo(({ sale, onStatusChange, isUpdatingStatus }) => {
  return (
    <tr>
      <td>{sale.displayId}</td>
      <td>{sale.createdAt}</td>
      <td>
        <StatusBadge 
          text={sale.statusDisplay} 
          className={sale.statusClassName} 
        />
      </td>
      <td>{sale.totalAmount}</td>
      <td>
        {sale.canChangeStatus ? (
          <OrderStatusDropdown 
            orderId={sale.id}
            currentStatus={sale.status}
            nextStatusOptions={sale.nextStatusOptions}
            onChange={onStatusChange}
            isLoading={isUpdatingStatus}
          />
        ) : (
          <span className="text-muted">-</span>
        )}
      </td>
    </tr>
  );
});

SaleItem.propTypes = {
  sale: PropTypes.shape({
    id: PropTypes.string.isRequired,
    displayId: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    statusDisplay: PropTypes.string.isRequired,
    statusClassName: PropTypes.string.isRequired,
    totalAmount: PropTypes.string.isRequired,
    createdAt: PropTypes.string.isRequired,
    canChangeStatus: PropTypes.bool.isRequired,
    nextStatusOptions: PropTypes.arrayOf(
      PropTypes.shape({
        value: PropTypes.string.isRequired,
        label: PropTypes.string.isRequired
      })
    ).isRequired
  }).isRequired,
  onStatusChange: PropTypes.func.isRequired,
  isUpdatingStatus: PropTypes.bool
};

SaleItem.defaultProps = {
  isUpdatingStatus: false
};

SaleItem.displayName = 'SaleItem';

export default SaleItem; 