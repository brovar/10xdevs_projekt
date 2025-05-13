import React from 'react';
import { useParams, Link } from 'react-router-dom';

const AdminOrderDetailPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  
  return (
    <div className="container py-4">
      <div className="row mb-4">
        <div className="col">
          <Link to="/admin?tab=orders" className="btn btn-outline-secondary mb-3">
            &laquo; Powrót do listy zamówień
          </Link>
          <h1>Szczegóły Zamówienia</h1>
          <p className="text-muted">ID: {orderId}</p>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          <div className="alert alert-info">
            <h4 className="alert-heading">Szczegóły Zamówienia</h4>
            <p>Ten widok będzie wyświetlał szczegółowe informacje o zamówieniu, w tym listę produktów i opcję anulowania.</p>
            <hr />
            <p className="mb-0">Funkcjonalność zostanie zaimplementowana w kolejnym kroku.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminOrderDetailPage; 