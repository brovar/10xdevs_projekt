import React, { useState } from 'react';

interface ErrorMessageDisplayProps {
  error: Error | string | null;
  className?: string;
  onRetry?: () => void;
  showDetails?: boolean;
}

const ErrorMessageDisplay: React.FC<ErrorMessageDisplayProps> = ({ 
  error, 
  className = '',
  onRetry,
  showDetails = false
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (!error) return null;

  // Extract error message and details
  let errorMessage = '';
  let errorDetails = '';
  
  if (typeof error === 'string') {
    errorMessage = error;
  } else {
    errorMessage = error.message;
    // Get the stack trace as details if available
    errorDetails = error.stack?.replace(error.message, '') || '';
  }
  
  // Toggle details visibility
  const toggleDetails = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <div 
      className={`alert alert-danger ${className}`} 
      role="alert"
      aria-live="assertive"
    >
      <div className="d-flex align-items-center">
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="24" 
          height="24" 
          fill="currentColor" 
          className="bi bi-exclamation-triangle-fill flex-shrink-0 me-2" 
          viewBox="0 0 16 16" 
          aria-hidden="true">
          <path d="M8.982 1.566a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5c.535 0 .954.462.9.995l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995A.905.905 0 0 1 8 5zm.002 6a1 1 0 1 1 0 2 1 1 0 0 1 0-2z"/>
        </svg>
        <div>
          <strong>Błąd: </strong>{errorMessage}
          
          {/* Action buttons */}
          <div className="mt-2 d-flex gap-2">
            {/* Retry button if onRetry function is provided */}
            {onRetry && (
              <button 
                type="button" 
                className="btn btn-sm btn-outline-danger" 
                onClick={onRetry}
                aria-label="Spróbuj ponownie"
              >
                <i className="bi bi-arrow-repeat me-1"></i>
                Spróbuj ponownie
              </button>
            )}
            
            {/* Details toggle button */}
            {showDetails && errorDetails && (
              <button 
                type="button" 
                className="btn btn-sm btn-outline-secondary" 
                onClick={toggleDetails}
                aria-expanded={isExpanded}
                aria-controls="errorDetails"
              >
                {isExpanded ? 'Ukryj szczegóły' : 'Pokaż szczegóły'}
              </button>
            )}
          </div>
          
          {/* Error details section */}
          {showDetails && errorDetails && isExpanded && (
            <div id="errorDetails" className="mt-3">
              <h6>Szczegóły błędu:</h6>
              <pre className="border rounded bg-light p-2 text-wrap" style={{ fontSize: '0.8rem' }}>
                {errorDetails}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorMessageDisplay; 