import React, { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';
import ConfirmLogoutModal from '../../components/common/ConfirmLogoutModal';

const LogoutPage = () => {
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(true);
  const { isAuthenticated, logout } = useAuth();
  const { addSuccess, addError } = useNotifications();
  const navigate = useNavigate();

  // Jeśli użytkownik nie jest zalogowany, od razu przekieruj do logowania
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  const handleConfirmLogout = async () => {
    setShowConfirmModal(false);
    setIsLoggingOut(true);

    try {
      const result = await logout();
      
      // Poprawne wylogowanie
      addSuccess('Wylogowano pomyślnie.');
      // Przekierowanie obsłużone przez zmianę stanu isLoggingOut
    } catch (error) {
      // Obsługa różnych rodzajów błędów
      let errorMessage = 'Wystąpił błąd podczas wylogowywania. Spróbuj ponownie później.';
      
      if (error.response) {
        // Odpowiedź z serwera zawiera błąd
        if (error.response.status === 401) {
          // Sesja już wygasła lub użytkownik nie jest zalogowany
          errorMessage = 'Sesja wygasła lub została już zakończona. Nastąpi przekierowanie.';
          // Czyścimy dane sesji lokalnie, ponieważ serwer uznaje że już nie jesteśmy zalogowani
          logout().catch(() => {
            // Ignorujemy potencjalne błędy czyszczenia, i tak przekierowujemy
          }).finally(() => {
            setTimeout(() => {
              navigate('/login');
            }, 2000);
          });
          addError(errorMessage);
          return;
        } else if (error.response.data?.message) {
          // Użyj komunikatu błędu z backendu jeśli jest dostępny
          errorMessage = error.response.data.message;
        }
      }
      
      addError(errorMessage);
      
      // Wróć do poprzedniej strony w przypadku błędu
      setTimeout(() => {
        navigate(-1);
      }, 2000);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleCancelLogout = () => {
    // Przekieruj z powrotem do poprzedniej strony lub na stronę główną
    navigate(-1);
  };

  // Jeśli proces wylogowania zakończony, przekieruj do logowania
  if (!isLoggingOut && !showConfirmModal) {
    return <Navigate to="/login" replace />;
  }

  return (
    <>
      <ConfirmLogoutModal 
        isOpen={showConfirmModal}
        onConfirm={handleConfirmLogout}
        onCancel={handleCancelLogout}
      />
      
      {isLoggingOut && (
        <div className="container mt-5 text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Wylogowywanie...</span>
          </div>
          <h2 className="mt-3">Wylogowywanie...</h2>
          <p>Proszę czekać, trwa wylogowywanie z systemu.</p>
        </div>
      )}
    </>
  );
};

export default LogoutPage; 