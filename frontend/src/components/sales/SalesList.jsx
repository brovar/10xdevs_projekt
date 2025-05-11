import React from 'react';
import PropTypes from 'prop-types';
import SaleItem from './SaleItem';
import { Table, Placeholder } from 'react-bootstrap';

/**
 * SalesList component for displaying a table of sales
 * 
 * @param {Object} props - Component props
 * @param {Array} props.sales - Array of sale items
 * @param {boolean} props.isLoading - Whether data is loading
 * @param {Function} props.onStatusChange - Handler for status change
 * @param {Object} props.updatingStatusMap - Map of order IDs to loading states
 * @returns {JSX.Element} - Rendered component
 */
const SalesList = React.memo(({ sales, isLoading, onStatusChange, updatingStatusMap }) => {
  // If there are no sales, display a message
  if (!isLoading && (!sales || sales.length === 0)) {
    return (
      <div className="alert alert-info" role="alert">
        Brak historii sprzedaży.
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <Table striped hover responsive>
        <thead className="table-light">
          <tr>
            <th>ID Zamówienia</th>
            <th>Data</th>
            <th>Status</th>
            <th>Kwota</th>
            <th>Akcje</th>
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            // Loading skeleton
            Array.from({ length: 5 }).map((_, index) => (
              <tr key={`skeleton-${index}`} className="opacity-50">
                <td><Placeholder xs={6} /></td>
                <td><Placeholder xs={8} /></td>
                <td><Placeholder xs={4} /></td>
                <td><Placeholder xs={5} /></td>
                <td><Placeholder xs={7} /></td>
              </tr>
            ))
          ) : (
            // Actual data
            sales.map(sale => (
              <SaleItem
                key={sale.id}
                sale={sale}
                onStatusChange={onStatusChange}
                isUpdatingStatus={updatingStatusMap[sale.id] || false}
              />
            ))
          )}
        </tbody>
      </Table>
    </div>
  );
});

SalesList.propTypes = {
  sales: PropTypes.array,
  isLoading: PropTypes.bool,
  onStatusChange: PropTypes.func.isRequired,
  updatingStatusMap: PropTypes.object
};

SalesList.defaultProps = {
  sales: [],
  isLoading: false,
  updatingStatusMap: {}
};

SalesList.displayName = 'SalesList';

export default SalesList; 