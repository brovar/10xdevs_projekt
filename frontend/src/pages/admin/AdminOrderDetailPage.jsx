import React from 'react';
import { useParams, Link } from 'react-router-dom';

const AdminOrderDetailPage = () => {
  const { orderId } = useParams();
  
  return (
    <div className="container py-4">
      <div className="row mb-4">
        <div className="col">
          <Link to="/admin?tab=orders" className="btn btn-outline-secondary mb-3">
            &laquo; Powrót do listy zamówień
          </Link>
          <h1>Szczegóły Zamówienia</h1>
          {orderId && <p className="text-muted">ID: {orderId}</p>}
        </div>
      </div>
      
      <div className="alert alert-info">
        Ładowanie szczegółów zamówienia...
      </div>
    </div>
  );
};

export default AdminOrderDetailPage; 