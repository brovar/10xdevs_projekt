import React from 'react';
import { Link } from 'react-router-dom';
import { OrderSummaryDTO, OrderStatus } from '../../../types/api';

interface OrderCancelActionProps {
  order: OrderSummaryDTO;
  onCancel: (orderId: string) => void;
}

const OrderCancelAction: React.FC<OrderCancelActionProps> = ({ order, onCancel }) => {
  // Determine if the order can be cancelled based on status
  const canBeCancelled = [
    OrderStatus.PENDING_PAYMENT,
    OrderStatus.PROCESSING,
    OrderStatus.SHIPPED
  ].includes(order.status);
  
  return (
    <div className="d-flex gap-2">
      {/* View details button */}
      <Link 
        to={`/admin/orders/${order.id}`} 
        className="btn btn-sm btn-outline-primary"
        aria-label={`View details of order ${order.id}`}
      >
        <i className="bi bi-eye"></i> Details
      </Link>
      
      {/* Cancel button - only shown for orders that can be cancelled */}
      {canBeCancelled && (
        <button
          type="button"
          className="btn btn-sm btn-danger"
          onClick={() => onCancel(order.id)}
          aria-label={`Cancel order ${order.id}`}
        >
          <i className="bi bi-x-circle"></i> Cancel
        </button>
      )}
    </div>
  );
};

export default OrderCancelAction; 