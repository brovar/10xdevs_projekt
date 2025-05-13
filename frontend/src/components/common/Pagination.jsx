import React, { useMemo } from 'react';
import PropTypes from 'prop-types';

const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  // Generate array of page numbers to display
  const pageNumbers = useMemo(() => {
    const pages = [];
    
    // Always show first and last page
    // For small number of pages, show all
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // For larger number of pages, use ellipsis
      pages.push(1); // Always show first page
      
      // Determine range around current page
      let startPage = Math.max(2, currentPage - 2);
      let endPage = Math.min(totalPages - 1, currentPage + 2);
      
      // Adjust range if we're near the beginning or end
      if (currentPage <= 4) {
        endPage = 5;
      } else if (currentPage >= totalPages - 3) {
        startPage = totalPages - 4;
      }
      
      // Add ellipsis before range if needed
      if (startPage > 2) {
        pages.push('...');
      }
      
      // Add page numbers in the range
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
      
      // Add ellipsis after range if needed
      if (endPage < totalPages - 1) {
        pages.push('...');
      }
      
      pages.push(totalPages); // Always show last page
    }
    
    return pages;
  }, [currentPage, totalPages]);

  return (
    <nav aria-label="Nawigacja paginacji">
      <ul className="pagination">
        {/* Previous page button */}
        <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
          <button
            className="page-link"
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            aria-label="Poprzednia strona"
          >
            &laquo;
          </button>
        </li>
        
        {/* Page numbers */}
        {pageNumbers.map((page, index) => (
          <li
            key={index}
            className={`page-item ${page === currentPage ? 'active' : ''} ${page === '...' ? 'disabled' : ''}`}
          >
            {page === '...' ? (
              <span className="page-link">...</span>
            ) : (
              <button
                className="page-link"
                onClick={() => onPageChange(page)}
                aria-label={`Strona ${page}`}
                aria-current={page === currentPage ? 'page' : undefined}
              >
                {page}
              </button>
            )}
          </li>
        ))}
        
        {/* Next page button */}
        <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
          <button
            className="page-link"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            aria-label="Następna strona"
          >
            &raquo;
          </button>
        </li>
      </ul>
    </nav>
  );
};

Pagination.propTypes = {
  currentPage: PropTypes.number.isRequired,
  totalPages: PropTypes.number.isRequired,
  onPageChange: PropTypes.func.isRequired
};

export default Pagination;