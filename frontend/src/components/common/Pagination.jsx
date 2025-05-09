import React, { useMemo } from 'react';
import PropTypes from 'prop-types';
import { Pagination as BsPagination } from 'react-bootstrap';

/**
 * Pagination component for navigating through pages of data
 * 
 * @param {Object} props
 * @param {number} props.currentPage - Current active page (1-based)
 * @param {number} props.totalPages - Total number of pages
 * @param {Function} props.onPageChange - Callback when page is changed
 * @param {number} [props.maxVisiblePages=5] - Maximum number of page buttons to show
 */
const Pagination = ({ 
  currentPage, 
  totalPages, 
  onPageChange,
  maxVisiblePages = 5
}) => {
  // Calculate which page buttons to show
  const pageButtons = useMemo(() => {
    let pages = [];
    
    // If we have fewer pages than max visible, show all pages
    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
      return pages;
    }
    
    // Calculate start and end page numbers for display
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = startPage + maxVisiblePages - 1;
    
    // Adjust if endPage exceeds totalPages
    if (endPage > totalPages) {
      endPage = totalPages;
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // Generate page numbers
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return pages;
  }, [currentPage, totalPages, maxVisiblePages]);

  const handlePageClick = (page) => {
    if (page !== currentPage && page >= 1 && page <= totalPages) {
      onPageChange(page);
    }
  };

  // Don't render pagination if only one page
  if (totalPages <= 1) {
    return null;
  }

  return (
    <BsPagination className="justify-content-center my-4">
      {/* First Page */}
      <BsPagination.First 
        onClick={() => handlePageClick(1)}
        disabled={currentPage === 1}
        aria-label="Pierwsza strona"
      />
      
      {/* Previous Page */}
      <BsPagination.Prev 
        onClick={() => handlePageClick(currentPage - 1)} 
        disabled={currentPage === 1}
        aria-label="Poprzednia strona"
      />
      
      {/* Show ellipsis if not starting from page 1 */}
      {pageButtons[0] > 1 && (
        <BsPagination.Ellipsis disabled aria-hidden="true" />
      )}
      
      {/* Page numbers */}
      {pageButtons.map(page => (
        <BsPagination.Item
          key={page}
          active={page === currentPage}
          onClick={() => handlePageClick(page)}
          aria-label={`Strona ${page}`}
          aria-current={page === currentPage ? 'page' : undefined}
        >
          {page}
        </BsPagination.Item>
      ))}
      
      {/* Show ellipsis if not ending at last page */}
      {pageButtons[pageButtons.length - 1] < totalPages && (
        <BsPagination.Ellipsis disabled aria-hidden="true" />
      )}
      
      {/* Next Page */}
      <BsPagination.Next 
        onClick={() => handlePageClick(currentPage + 1)} 
        disabled={currentPage === totalPages}
        aria-label="Następna strona" 
      />
      
      {/* Last Page */}
      <BsPagination.Last 
        onClick={() => handlePageClick(totalPages)}
        disabled={currentPage === totalPages}
        aria-label="Ostatnia strona"
      />
    </BsPagination>
  );
};

Pagination.propTypes = {
  currentPage: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  onPageChange: PropTypes.func.isRequired,
  maxVisiblePages: PropTypes.number
};

export default React.memo(Pagination); 