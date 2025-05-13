import React from 'react';

interface PaginationInfo {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  limit: number;
}

interface PaginationComponentProps {
  paginationInfo: PaginationInfo;
  onPageChange: (page: number) => void;
  className?: string;
  ariaLabel?: string;
}

const PaginationComponent: React.FC<PaginationComponentProps> = ({
  paginationInfo,
  onPageChange,
  className = '',
  ariaLabel = 'Nawigacja stronicowania'
}) => {
  const { currentPage, totalPages, totalItems, limit } = paginationInfo;

  // Don't show pagination if there's only 1 page
  if (totalPages <= 1) return null;

  // Generate page numbers array
  const getPageNumbers = () => {
    const pages: number[] = []; // Explicitly type the array as number[]
    const maxVisiblePages = 5; // Number of page buttons to show
    
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    // Adjust if we're at the end
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    return pages;
  };
  
  const pageNumbers = getPageNumbers();
  
  // Calculate displayed item range for the current page
  const startItem = (currentPage - 1) * limit + 1;
  // Explicitly provide numbers for Math.min to resolve type issue
  const endItem = Math.min(Number(currentPage * limit), Number(totalItems));
  
  // Handle key navigation for pagination
  const handleKeyDown = (e: React.KeyboardEvent, targetPage: number) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onPageChange(targetPage);
    }
  };

  return (
    <nav 
      aria-label={ariaLabel} 
      className={className}
    >
      <div className="d-flex justify-content-between align-items-center mb-2">
        {/* Status info for screen readers and all users */}
        <p className="mb-0" aria-live="polite">
          <span className="visually-hidden">Obecnie wyświetlane: </span>
          Pozycje {startItem}-{endItem} z {totalItems}
        </p>
        
        {/* Total pages count */}
        <p className="mb-0">
          Strona {currentPage} z {totalPages}
        </p>
      </div>
      
      <ul className="pagination justify-content-center">
        {/* Previous page */}
        <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
          <button
            className="page-link"
            onClick={() => onPageChange(currentPage - 1)}
            onKeyDown={(e) => handleKeyDown(e, currentPage - 1)}
            disabled={currentPage === 1}
            aria-label="Przejdź do poprzedniej strony"
            aria-disabled={currentPage === 1}
          >
            <span aria-hidden="true">&laquo;</span>
            <span className="visually-hidden">Poprzednia</span>
          </button>
        </li>
        
        {/* First page */}
        {pageNumbers[0] > 1 && (
          <>
            <li className="page-item">
              <button 
                className="page-link" 
                onClick={() => onPageChange(1)}
                onKeyDown={(e) => handleKeyDown(e, 1)}
                aria-label="Przejdź do pierwszej strony"
              >
                1
              </button>
            </li>
            {pageNumbers[0] > 2 && (
              <li className="page-item disabled">
                <span className="page-link" aria-hidden="true">...</span>
              </li>
            )}
          </>
        )}
        
        {/* Page numbers */}
        {pageNumbers.map(page => (
          <li 
            key={page} 
            className={`page-item ${page === currentPage ? 'active' : ''}`}
          >
            <button
              className="page-link"
              onClick={() => onPageChange(page)}
              onKeyDown={(e) => handleKeyDown(e, page)}
              aria-label={`Przejdź do strony ${page}`}
              aria-current={page === currentPage ? 'page' : undefined}
            >
              {page}
            </button>
          </li>
        ))}
        
        {/* Last page */}
        {pageNumbers[pageNumbers.length - 1] < totalPages && (
          <>
            {pageNumbers[pageNumbers.length - 1] < totalPages - 1 && (
              <li className="page-item disabled">
                <span className="page-link" aria-hidden="true">...</span>
              </li>
            )}
            <li className="page-item">
              <button
                className="page-link"
                onClick={() => onPageChange(totalPages)}
                onKeyDown={(e) => handleKeyDown(e, totalPages)}
                aria-label={`Przejdź do ostatniej strony (${totalPages})`}
              >
                {totalPages}
              </button>
            </li>
          </>
        )}
        
        {/* Next page */}
        <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
          <button
            className="page-link"
            onClick={() => onPageChange(currentPage + 1)}
            onKeyDown={(e) => handleKeyDown(e, currentPage + 1)}
            disabled={currentPage === totalPages}
            aria-label="Przejdź do następnej strony"
            aria-disabled={currentPage === totalPages}
          >
            <span aria-hidden="true">&raquo;</span>
            <span className="visually-hidden">Następna</span>
          </button>
        </li>
      </ul>
    </nav>
  );
};

export default PaginationComponent; 