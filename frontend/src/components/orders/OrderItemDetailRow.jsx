import React from 'react';
import PropTypes from 'prop-types';

/**
 * OrderItemDetailRow displays a single item in an order as a table row
 * 
 * @param {Object} props
 * @param {Object} props.item - Order item data
 */
const OrderItemDetailRow = ({ item }) => {
  return (
    <tr>
      <td>{item.offerTitle}</td>
      <td className="text-center">{item.quantity}</td>
      <td className="text-end">{item.priceAtPurchaseFormatted}</td>
      <td className="text-end fw-bold">{item.itemSumFormatted}</td>
    </tr>
  );
};

OrderItemDetailRow.propTypes = {
  item: PropTypes.shape({
    id: PropTypes.number.isRequired,
    offerId: PropTypes.string.isRequired,
    offerTitle: PropTypes.string.isRequired,
    quantity: PropTypes.number.isRequired,
    priceAtPurchaseFormatted: PropTypes.string.isRequired,
    itemSumFormatted: PropTypes.string.isRequired
  }).isRequired
};

export default React.memo(OrderItemDetailRow); 