import React, { useMemo } from 'react';
import { OrderSummaryDTO } from '../../../types/api';
import StatusBadge from '../../shared/StatusBadge.tsx';
import OrderCancelAction from './OrderCancelAction.tsx';

interface AdminOrderListTableProps {
  orders: OrderSummaryDTO[];
  onCancel: (orderId: string) => void;
}

const AdminOrderListTable: React.FC<AdminOrderListTableProps> = ({
  orders,
  onCancel
}) => {
  // Format date - memoized to avoid unnecessary recalculations
  const formatDate = useMemo(() => {
    return (dateString: string) => {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('en-US', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    };
  }, []);

  // Format price - memoized to avoid unnecessary recalculations
  const formatPrice = useMemo(() => {
    return (price: string) => {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
      }).format(parseFloat(price));
    };
  }, []);

  if (orders.length === 0) {
    return (
      <div className="alert alert-info">
        No orders matching search criteria.
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <table className="table table-striped table-hover">
        <thead className="table-light">
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Status</th>
            <th scope="col">Amount</th>
            <th scope="col">Created at</th>
            <th scope="col">Updated at</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {orders.map(order => (
            <tr key={order.id}>
              <td>
                <small className="text-muted">{order.id.slice(0, 8)}...</small>
              </td>
              <td>
                <StatusBadge status={order.status} />
              </td>
              <td>{formatPrice(order.total_amount)}</td>
              <td>{formatDate(order.created_at)}</td>
              <td>{order.updated_at ? formatDate(order.updated_at) : '-'}</td>
              <td>
                <OrderCancelAction 
                  order={order}
                  onCancel={onCancel}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AdminOrderListTable; 