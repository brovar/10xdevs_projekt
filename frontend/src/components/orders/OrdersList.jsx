import React from 'react';
import PropTypes from 'prop-types';
import { Table } from 'react-bootstrap';
import OrderItem from './OrderItem';

/**
 * OrdersList component renders a table of orders
 * 
 * @param {Object} props
 * @param {Array} props.orders - Array of order data in ViewModel format
 * @param {boolean} [props.isLoading] - Whether the list is loading
 */
const OrdersList = ({ orders, isLoading = false }) => {
  return (
    <Table responsive striped hover className="mt-4">
      <thead>
        <tr>
          <th>Order number</th>
          <th>Date</th>
          <th>Number of products</th>
          <th>Amount</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {orders.map(order => (
          <OrderItem key={order.id} order={order} />
        ))}
        {isLoading && (
          <tr>
            <td colSpan={6} className="text-center py-3">
              <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              Loading orders...
            </td>
          </tr>
        )}
        {!isLoading && orders.length === 0 && (
          <tr>
            <td colSpan={6} className="text-center py-3">
              No orders to display
            </td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

OrdersList.propTypes = {
  orders: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      displayId: PropTypes.string.isRequired,
      status: PropTypes.string.isRequired,
      totalAmount: PropTypes.string.isRequired,
      createdAt: PropTypes.string.isRequired,
      detailsLink: PropTypes.string.isRequired,
      itemsCount: PropTypes.number.isRequired
    })
  ).isRequired,
  isLoading: PropTypes.bool
};

export default React.memo(OrdersList); 