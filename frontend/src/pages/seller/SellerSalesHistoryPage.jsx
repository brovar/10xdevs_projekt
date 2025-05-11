import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams, Navigate } from 'react-router-dom';
import { Toast, ToastContainer, Container } from 'react-bootstrap';
import { useAuth } from '../../contexts/AuthContext';

// Importujemy wszystkie potrzebne komponenty
// Jeśli te komponenty nie istnieją w tej strukturze katalogów, będziemy musieli je zaimplementować tu również
import SortControls from '../../components/sales/SortControls';
import SalesList from '../../components/sales/SalesList';
import Pagination from '../../components/common/Pagination';

// Serwis i funkcje pomocnicze
import { fetchSalesHistory, updateOrderStatus } from '../../services/salesService';
import { mapOrderSummaryToSaleItemVM } from '../../utils/orderUtils';

/**
 * SalesHistoryPage component for viewing sales history (for sellers only)
 * 
 * @returns {JSX.Element} - Rendered component
 */
const SellerSalesHistoryPage = () => {
  // Get auth context
  const { isAuthenticated, user, isLoading: authLoading } = useAuth();
  
  // URL search params for page and sort
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Component state
  const [sales, setSales] = useState([]);
  const [paginationData, setPaginationData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingStatusMap, setUpdatingStatusMap] = useState({});
  const [toast, setToast] = useState({ show: false, message: '', variant: 'success' });
  
  // Get current sort and page from URL or use defaults
  const currentSort = searchParams.get('sort') || 'created_at_desc';
  const currentPage = parseInt(searchParams.get('page') || '1', 10);
  
  // Sort options for dropdown
  const sortOptions = useMemo(() => {
    return [
      { value: 'created_at_desc', label: 'Data utworzenia (najnowsze)' },
      { value: 'created_at_asc', label: 'Data utworzenia (najstarsze)' },
      { value: 'updated_at_desc', label: 'Data aktualizacji (najnowsze)' },
      { value: 'updated_at_asc', label: 'Data aktualizacji (najstarsze)' },
      { value: 'total_amount_desc', label: 'Kwota (od najwyższej)' },
      { value: 'total_amount_asc', label: 'Kwota (od najniższej)' },
      { value: 'status_desc', label: 'Status (Z-A)' },
      { value: 'status_asc', label: 'Status (A-Z)' }
    ];
  }, []);
  
  // Fetch sales data on component mount or when search params change
  useEffect(() => {
    // Don't fetch if not authenticated yet
    if (authLoading || !isAuthenticated || user?.role !== 'Seller') {
      return;
    }
    
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const response = await fetchSalesHistory({
          page: currentPage,
          limit: 10,
          sort: currentSort
        });
        
        // Map API response to view models
        const salesData = response.items.map(mapOrderSummaryToSaleItemVM);
        
        setSales(salesData);
        setPaginationData({
          currentPage: response.page,
          totalPages: response.pages,
          totalItems: response.total
        });
      } catch (err) {
        console.error('Error fetching sales data:', err);
        setError('Nie udało się załadować historii sprzedaży.');
        setToast({
          show: true,
          message: 'Nie udało się załadować historii sprzedaży.',
          variant: 'danger'
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [currentPage, currentSort, isAuthenticated, user, authLoading]);
  
  // Handle sort change
  const handleSortChange = (sortValue) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('sort', sortValue);
    newParams.set('page', '1'); // Reset to page 1 when changing sort
    setSearchParams(newParams);
  };
  
  // Handle page change
  const handlePageChange = (page) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', page.toString());
    setSearchParams(newParams);
  };
  
  // Handle status change
  const handleStatusChange = async (orderId, newStatus) => {
    // Set loading state for this specific order
    setUpdatingStatusMap(prev => ({ ...prev, [orderId]: true }));
    
    try {
      // Call API to update status (note: this is currently mocked)
      await updateOrderStatus(orderId, { status: newStatus });
      
      // Update local state to reflect the change
      setSales(prevSales => 
        prevSales.map(sale => {
          if (sale.id === orderId) {
            // Get next status options from orderUtils
            const updatedSale = mapOrderSummaryToSaleItemVM({ 
              ...sale, 
              status: newStatus,
              // Update timestamp
              updated_at: new Date().toISOString()
            });
            return updatedSale;
          }
          return sale;
        })
      );
      
      // Show success message
      setToast({
        show: true,
        message: 'Status zamówienia został zaktualizowany.',
        variant: 'success'
      });
    } catch (err) {
      console.error('Error updating order status:', err);
      setToast({
        show: true,
        message: 'Nie udało się zmienić statusu zamówienia.',
        variant: 'danger'
      });
    } finally {
      setUpdatingStatusMap(prev => ({ ...prev, [orderId]: false }));
    }
  };
  
  // Show loading state while auth is being checked
  if (authLoading) {
    return (
      <Container className="py-5">
        <div className="d-flex justify-content-center">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Ładowanie...</span>
          </div>
        </div>
      </Container>
    );
  }
  
  // Redirect if not authenticated or not a seller
  if (!isAuthenticated || user?.role !== 'Seller') {
    return <Navigate to="/login" replace state={{ from: '/seller/sales' }} />;
  }
  
  return (
    <Container className="py-4">
      <h1 className="mb-4">Historia Sprzedaży</h1>
      
      {/* Toast notification */}
      <ToastContainer position="top-end" className="p-3">
        <Toast 
          show={toast.show} 
          onClose={() => setToast(prev => ({ ...prev, show: false }))} 
          delay={5000} 
          autohide
          bg={toast.variant}
        >
          <Toast.Header closeButton>
            <strong className="me-auto">
              {toast.variant === 'success' ? 'Sukces' : 'Błąd'}
            </strong>
          </Toast.Header>
          <Toast.Body className={toast.variant === 'success' ? '' : 'text-white'}>
            {toast.message}
          </Toast.Body>
        </Toast>
      </ToastContainer>
      
      {/* Sorting controls */}
      <SortControls 
        options={sortOptions}
        currentSort={currentSort}
        onSortChange={handleSortChange}
      />
      
      {/* Error message */}
      {error && !isLoading && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}
      
      {/* Sales list */}
      <SalesList 
        sales={sales}
        isLoading={isLoading}
        onStatusChange={handleStatusChange}
        updatingStatusMap={updatingStatusMap}
      />
      
      {/* Pagination */}
      {paginationData && (
        <div className="d-flex justify-content-center mt-4">
          <Pagination 
            currentPage={paginationData.currentPage}
            totalPages={paginationData.totalPages}
            onPageChange={handlePageChange}
          />
        </div>
      )}
    </Container>
  );
};

export default SellerSalesHistoryPage; 