import React, { useMemo } from 'react';
import PropTypes from 'prop-types';
import { Pagination as BsPagination } from 'react-bootstrap';

/**
 * Pagination component for navigating between pages of results
 * 
 * @param {Object} props - Component props
 * @param {number} props.currentPage - Current active page
 * @param {number} props.totalPages - Total number of pages available
 * @param {function} props.onPageChange - Handler for page change events
 * @returns {JSX.Element} - Rendered component
 */
const Pagination = React.memo(({ currentPage, totalPages, onPageChange }) => {
  // Generate page numbers to display with visible range and ellipsis
  const pageNumbers = useMemo(() => {
    // Always show first and last pages, and up to 3 pages around current page
    const visiblePages = [];
    const maxVisiblePages = 5;
    
    if (totalPages <= maxVisiblePages) {
      // If we have 5 or fewer pages, show all
      for (let i = 1; i <= totalPages; i++) {
        visiblePages.push(i);
      }
    } else {
      // Always show page 1
      visiblePages.push(1);
      
      // Show ellipsis if current page is more than 3
      if (currentPage > 3) {
        visiblePages.push('ellipsis-1');
      }
      
      // Show pages around current page
      const startPage = Math.max(2, currentPage - 1);
      const endPage = Math.min(totalPages - 1, currentPage + 1);
      
      for (let i = startPage; i <= endPage; i++) {
        visiblePages.push(i);
      }
      
      // Show ellipsis if current page is less than totalPages - 2
      if (currentPage < totalPages - 2) {
        visiblePages.push('ellipsis-2');
      }
      
      // Always show last page
      if (totalPages > 1) {
        visiblePages.push(totalPages);
      }
    }
    
    return visiblePages;
  }, [currentPage, totalPages]);
  
  // If there's only one page or no pages, don't render pagination
  if (totalPages <= 1) return null;
  
  return (
    <BsPagination aria-label="Nawigacja między stronami wyników">
      <BsPagination.Prev
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        aria-label="Poprzednia strona"
      />
      
      {pageNumbers.map((page, index) => {
        if (typeof page === 'string' && page.includes('ellipsis')) {
          return <BsPagination.Ellipsis key={page} disabled />;
        }
        
        return (
          <BsPagination.Item
            key={`page-${page}`}
            active={page === currentPage}
            onClick={() => onPageChange(page)}
            aria-label={`Przejdź do strony ${page}`}
            aria-current={page === currentPage ? 'page' : undefined}
          >
            {page}
          </BsPagination.Item>
        );
      })}
      
      <BsPagination.Next
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        aria-label="Następna strona"
      />
    </BsPagination>
  );
});

Pagination.propTypes = {
  currentPage: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  onPageChange: PropTypes.func.isRequired
};

Pagination.displayName = 'Pagination';

export default Pagination; 