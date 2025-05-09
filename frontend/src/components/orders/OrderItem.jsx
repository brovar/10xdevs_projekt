import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import StatusBadge from '../shared/StatusBadge';

/**
 * OrderItem component to display a single order in the orders list
 * 
 * @param {Object} props
 * @param {Object} props.order - Order data in ViewModel format
 */
const OrderItem = ({ order }) => {
  return (
    <tr>
      <td>{order.displayId}</td>
      <td>{order.createdAt}</td>
      <td>{order.itemsCount}</td>
      <td>{order.totalAmount}</td>
      <td>
        <StatusBadge status={order.status} />
      </td>
      <td>
        <Link 
          to={order.detailsLink} 
          className="btn btn-sm btn-outline-primary"
          aria-label={`Zobacz szczegóły zamówienia ${order.displayId}`}
        >
          Szczegóły
        </Link>
      </td>
    </tr>
  );
};

OrderItem.propTypes = {
  order: PropTypes.shape({
    id: PropTypes.string.isRequired,
    displayId: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    totalAmount: PropTypes.string.isRequired,
    createdAt: PropTypes.string.isRequired,
    detailsLink: PropTypes.string.isRequired,
    itemsCount: PropTypes.number.isRequired
  }).isRequired
};

export default React.memo(OrderItem); 