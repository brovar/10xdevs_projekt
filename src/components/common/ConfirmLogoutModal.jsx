import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

const ConfirmLogoutModal = ({ isOpen, onConfirm, onCancel }) => {
  const confirmButtonRef = useRef(null);
  const modalRef = useRef(null);
  
  // Focus na przycisku potwierdzenia przy otwarciu modalu
  useEffect(() => {
    if (isOpen && confirmButtonRef.current) {
      confirmButtonRef.current.focus();
    }
  }, [isOpen]);

  // Dodanie obsługi klawisza Escape do zamknięcia modalu
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

  // Zatrzymanie focus wewnątrz modalu (focus trap)
  useEffect(() => {
    if (!isOpen || !modalRef.current) return;

    const focusableElements = modalRef.current.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
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

    modalRef.current.addEventListener('keydown', handleTabKey);
    return () => {
      if (modalRef.current) {
        modalRef.current.removeEventListener('keydown', handleTabKey);
      }
    };
  }, [isOpen]);

  // Zapobieganie przewijaniu strony gdy modal jest otwarty
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

  return (
    <div 
      className="modal fade show" 
      tabIndex="-1" 
      role="dialog" 
      aria-modal="true"
      aria-labelledby="logout-modal-title"
      style={{ display: 'block' }}
      ref={modalRef}
    >
      <div className="modal-dialog modal-dialog-centered" role="document">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title" id="logout-modal-title">
              Potwierdzenie wylogowania
            </h5>
            <button
              type="button"
              className="btn-close"
              aria-label="Zamknij"
              onClick={onCancel}
            ></button>
          </div>
          <div className="modal-body">
            <p>Czy na pewno chcesz się wylogować z systemu?</p>
            <p className="text-muted">
              Po wylogowaniu konieczne będzie ponowne zalogowanie, aby uzyskać dostęp do systemu.
            </p>
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onCancel}
            >
              Anuluj
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={onConfirm}
              ref={confirmButtonRef}
            >
              Wyloguj
            </button>
          </div>
        </div>
      </div>
      <div className="modal-backdrop fade show"></div>
    </div>
  );
};

ConfirmLogoutModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onConfirm: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired
};

export default React.memo(ConfirmLogoutModal); 