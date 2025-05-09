import React from 'react';
import PropTypes from 'prop-types';
import { Card } from 'react-bootstrap';
import StatusBadge from '../shared/StatusBadge';

/**
 * OrderDetailsPanel displays general information about an order
 * 
 * @param {Object} props
 * @param {Object} props.order - Order information
 */
const OrderDetailsPanel = ({ order }) => {
  if (!order) return null;

  return (
    <Card className="mb-4">
      <Card.Header as="h5">Informacje o zamówieniu</Card.Header>
      <Card.Body>
        <dl className="row mb-0">
          <dt className="col-sm-4">Numer zamówienia:</dt>
          <dd className="col-sm-8">{order.displayId}</dd>

          <dt className="col-sm-4">Data złożenia:</dt>
          <dd className="col-sm-8">{order.createdAt}</dd>

          <dt className="col-sm-4">Status:</dt>
          <dd className="col-sm-8">
            <StatusBadge status={order.status} />
          </dd>

          <dt className="col-sm-4">Łączna kwota:</dt>
          <dd className="col-sm-8 fw-bold">{order.totalAmount}</dd>
        </dl>
      </Card.Body>
    </Card>
  );
};

OrderDetailsPanel.propTypes = {
  order: PropTypes.shape({
    displayId: PropTypes.string.isRequired,
    createdAt: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    totalAmount: PropTypes.string.isRequired
  })
};

export default React.memo(OrderDetailsPanel); 