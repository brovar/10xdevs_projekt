import React, { useMemo } from 'react';
import { OfferSummaryDTO } from '../../../types/api';
import OfferModerationActions from './OfferModerationActions.tsx';
import StatusBadge from '../../shared/StatusBadge.tsx';

interface AdminOfferListTableProps {
  offers: OfferSummaryDTO[];
  onModerate: (offerId: string) => void;
  onUnmoderate: (offerId: string) => void;
}

const AdminOfferListTable: React.FC<AdminOfferListTableProps> = ({
  offers,
  onModerate,
  onUnmoderate
}) => {
  // Format date - memoized to avoid unnecessary recalculations
  const formatDate = useMemo(() => {
    return (dateString: string) => {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('pl-PL', {
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
      return new Intl.NumberFormat('pl-PL', {
        style: 'currency',
        currency: 'PLN'
      }).format(parseFloat(price));
    };
  }, []);

  if (offers.length === 0) {
    return (
      <div className="alert alert-info">
        Brak ofert spełniających kryteria wyszukiwania.
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <table className="table table-striped table-hover">
        <thead className="table-light">
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Tytuł</th>
            <th scope="col">Cena</th>
            <th scope="col">Ilość</th>
            <th scope="col">Kategoria</th>
            <th scope="col">Status</th>
            <th scope="col">Data utworzenia</th>
            <th scope="col">Akcje</th>
          </tr>
        </thead>
        <tbody>
          {offers.map(offer => (
            <tr key={offer.id}>
              <td>
                <small className="text-muted">{offer.id.slice(0, 8)}...</small>
              </td>
              <td>
                <span className="d-inline-block text-truncate" style={{maxWidth: '200px'}}>
                  {offer.title}
                </span>
              </td>
              <td>{formatPrice(offer.price)}</td>
              <td>{offer.quantity}</td>
              <td>{offer.category_id}</td>
              <td>
                <StatusBadge status={offer.status} />
              </td>
              <td>{formatDate(offer.created_at)}</td>
              <td>
                <OfferModerationActions 
                  offer={offer}
                  onModerate={onModerate}
                  onUnmoderate={onUnmoderate}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AdminOfferListTable; 