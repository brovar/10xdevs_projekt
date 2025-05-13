import React, { useEffect, useRef, useState } from 'react';

interface ConfirmationModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmButtonText?: string;
  cancelButtonText?: string;
  variant?: 'danger' | 'warning' | 'primary';
  isProcessing?: boolean;
  error?: string | null;
}

const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  title,
  message,
  onConfirm,
  onCancel,
  confirmButtonText = 'Potwierdź',
  cancelButtonText = 'Anuluj',
  variant = 'danger',
  isProcessing = false,
  error = null
}) => {
  // Keep track of the element to return focus to when modal closes
  const [returnFocusTo, setReturnFocusTo] = useState<HTMLElement | null>(null);
  
  // Create refs for focusable elements
  const modalRef = useRef<HTMLDivElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  const confirmButtonRef = useRef<HTMLButtonElement>(null);
  
  // Setup the focus trap when modal opens
  useEffect(() => {
    if (isOpen) {
      // Store the currently focused element to return to later
      setReturnFocusTo(document.activeElement as HTMLElement);
      
      // Focus the first interactive element (close button)
      setTimeout(() => {
        closeButtonRef.current?.focus();
      }, 50);
      
      // Add event listener for ESC key to close modal
      const handleKeyDown = (event: KeyboardEvent) => {
        if (event.key === 'Escape') {
          onCancel();
        }
      };
      
      window.addEventListener('keydown', handleKeyDown);
      
      // Prevent scrolling on the body
      document.body.style.overflow = 'hidden';
      
      return () => {
        // Cleanup
        window.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = '';
        
        // Return focus to the previous element
        setTimeout(() => {
          returnFocusTo?.focus();
        }, 50);
      };
    }
  }, [isOpen, onCancel, returnFocusTo]);
  
  // Handle tabbing in the modal to create a focus trap
  const handleTabKey = (event: React.KeyboardEvent) => {
    if (event.key !== 'Tab') return;
    
    const focusableElements = modalRef.current?.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (!focusableElements || focusableElements.length === 0) return;
    
    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
    
    // Shift+Tab from first element focuses the last element
    if (event.shiftKey && document.activeElement === firstElement) {
      lastElement.focus();
      event.preventDefault();
    } 
    // Tab from last element focuses the first element
    else if (!event.shiftKey && document.activeElement === lastElement) {
      firstElement.focus();
      event.preventDefault();
    }
  };

  if (!isOpen) return null;

  // Define button color based on variant
  const buttonColorClass = {
    danger: 'btn-danger',
    warning: 'btn-warning',
    primary: 'btn-primary'
  }[variant];

  return (
    <>
      {/* Modal Backdrop */}
      <div 
        className="modal-backdrop fade show" 
        onClick={onCancel}
        style={{ display: 'block' }}
      />
      
      {/* Modal Dialog */}
      <div 
        className="modal fade show" 
        tabIndex={-1} 
        role="dialog" 
        aria-modal="true"
        aria-labelledby="modalTitle"
        onKeyDown={handleTabKey}
        ref={modalRef}
        style={{ display: 'block' }}
      >
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title" id="modalTitle">{title}</h5>
              <button 
                type="button" 
                className="btn-close" 
                aria-label="Close" 
                onClick={onCancel}
                ref={closeButtonRef}
              />
            </div>
            <div className="modal-body">
              <p>{message}</p>
              
              {/* Error message if provided */}
              {error && (
                <div className="alert alert-danger mt-3" role="alert">
                  {error}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button 
                type="button" 
                className="btn btn-secondary" 
                onClick={onCancel}
                ref={cancelButtonRef}
                disabled={isProcessing}
              >
                {cancelButtonText}
              </button>
              <button 
                type="button" 
                className={`btn ${buttonColorClass}`} 
                onClick={onConfirm}
                ref={confirmButtonRef}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Przetwarzanie...
                  </>
                ) : confirmButtonText}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ConfirmationModal; 