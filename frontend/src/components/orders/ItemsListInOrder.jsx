import React from 'react';
import PropTypes from 'prop-types';
import { Table } from 'react-bootstrap';
import OrderItemDetailRow from './OrderItemDetailRow';

/**
 * ItemsListInOrder displays a table of items in an order
 * 
 * @param {Object} props
 * @param {Array} props.items - Array of order items
 */
const ItemsListInOrder = ({ items }) => {
  if (!items || items.length === 0) {
    return (
      <div className="alert alert-info">
        This order doesn't contain any products.
      </div>
    );
  }

  return (
    <Table responsive striped hover>
      <thead>
        <tr>
          <th>Product</th>
          <th className="text-center">Quantity</th>
          <th className="text-end">Unit price</th>
          <th className="text-end">Item total</th>
        </tr>
      </thead>
      <tbody>
        {items.map(item => (
          <OrderItemDetailRow key={item.id} item={item} />
        ))}
      </tbody>
    </Table>
  );
};

ItemsListInOrder.propTypes = {
  items: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      offerId: PropTypes.string.isRequired,
      offerTitle: PropTypes.string.isRequired,
      quantity: PropTypes.number.isRequired,
      priceAtPurchaseFormatted: PropTypes.string.isRequired,
      itemSumFormatted: PropTypes.string.isRequired
    })
  ).isRequired
};

export default React.memo(ItemsListInOrder); 