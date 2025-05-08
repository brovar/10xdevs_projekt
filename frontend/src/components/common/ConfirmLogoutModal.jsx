import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';
import ReactDOM from 'react-dom';

// Modal styles defined outside component to avoid recreation on each render
const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 999999
  },
  dialog: {
    backgroundColor: 'white',
    borderRadius: '5px',
    maxWidth: '500px',
    width: '100%',
    boxShadow: '0 5px 15px rgba(0, 0, 0, 0.5)',
    zIndex: 1000000,
    overflow: 'hidden'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem',
    borderBottom: '1px solid #e9ecef'
  },
  title: {
    margin: 0,
    fontWeight: 500,
    fontSize: '1.25rem'
  },
  closeButton: {
    cursor: 'pointer',
    border: 'none',
    backgroundColor: 'transparent',
    fontSize: '1.5rem',
    padding: '0',
    fontWeight: 'bold'
  },
  body: {
    padding: '1rem'
  },
  footer: {
    display: 'flex',
    justifyContent: 'flex-end',
    padding: '1rem',
    borderTop: '1px solid #e9ecef'
  },
  cancelButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '0.25rem',
    marginRight: '0.5rem',
    cursor: 'pointer'
  },
  confirmButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '0.25rem',
    cursor: 'pointer'
  },
  mutedText: {
    color: '#6c757d',
    fontSize: '0.875rem'
  }
};

const ConfirmLogoutModal = ({ isOpen, onConfirm, onCancel }) => {
  const confirmButtonRef = useRef(null);
  const modalRef = useRef(null);
  
  // Clean up any existing Bootstrap elements that may interfere
  useEffect(() => {
    if (isOpen) {
      // Cleanup function to remove bootstrap elements
      const cleanup = () => {
        document.querySelectorAll('.modal-backdrop').forEach(el => {
          el.parentNode.removeChild(el);
        });
        
        // Reset body classes that Bootstrap might have added
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
      };
      
      // Run cleanup immediately and schedule again to ensure it happens
      cleanup();
      
      // Set timeout to run cleanup again after any Bootstrap initialization
      const timeoutId = setTimeout(cleanup, 100);
      
      return () => {
        clearTimeout(timeoutId);
        cleanup();
      };
    }
  }, [isOpen]);
  
  // Focus on confirmation button when modal opens
  useEffect(() => {
    if (isOpen && confirmButtonRef.current) {
      confirmButtonRef.current.focus();
    }
  }, [isOpen]);

  // Add Escape key handler to close modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onCancel();
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onCancel]);

  // Focus trap within modal
  useEffect(() => {
    if (!isOpen || !modalRef.current) return;

    const modalElement = modalRef.current;
    const focusableElements = modalElement.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) return;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key !== 'Tab') return;
      
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    modalElement.addEventListener('keydown', handleTabKey);
    return () => {
      modalElement.removeEventListener('keydown', handleTabKey);
    };
  }, [isOpen]);

  // Prevent page scrolling when modal is open
  useEffect(() => {
    if (isOpen) {
      const originalStyle = window.getComputedStyle(document.body).overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalStyle;
      };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return ReactDOM.createPortal(
    <div style={styles.overlay} onClick={onCancel}>
      <div 
        style={styles.dialog} 
        onClick={(e) => e.stopPropagation()}
        ref={modalRef}
      >
        <div style={styles.header}>
          <h5 style={styles.title}>Potwierdzenie wylogowania</h5>
          <button
            style={styles.closeButton}
            onClick={onCancel}
            aria-label="Zamknij"
          >
            &times;
          </button>
        </div>
        
        <div style={styles.body}>
          <p>Czy na pewno chcesz się wylogować z systemu?</p>
          <p style={styles.mutedText}>
            Po wylogowaniu konieczne będzie ponowne zalogowanie, aby uzyskać dostęp do systemu.
          </p>
        </div>
        
        <div style={styles.footer}>
          <button
            style={styles.cancelButton}
            onClick={onCancel}
          >
            Anuluj
          </button>
          <button
            style={styles.confirmButton}
            onClick={onConfirm}
            ref={confirmButtonRef}
          >
            Wyloguj
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
};

ConfirmLogoutModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onConfirm: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired
};

export default React.memo(ConfirmLogoutModal); 