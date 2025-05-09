import React, { useEffect, useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useCart } from '../../contexts/CartContext';
import { useNotifications } from '../../contexts/NotificationContext';
import ConfirmLogoutModal from '../common/ConfirmLogoutModal';
import axios from '../../services/api';

const Header = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const { totalItems } = useCart();
  const { addSuccess, addError } = useNotifications();
  const navigate = useNavigate();
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  
  // Enhanced debug info
  useEffect(() => {
    console.log('Auth state in Header:', { 
      isAuthenticated, 
      user,
      hasRole: !!user?.role,
      role: user?.role,
      isBuyer: user?.role === 'Buyer',
      detailedUser: JSON.stringify(user)
    });
    
    // Po zmianie stanu uwierzytelnienia, sprawdź aktualny status użytkownika
    const checkCurrentUserStatus = async () => {
      if (isAuthenticated && (!user?.role || user?.role === '')) {
        try {
          console.log('Refreshing user data due to missing role');
          const response = await axios.get('/auth/status');
          if (response.data && response.data.is_authenticated && response.data.user) {
            const updatedUserData = response.data.user;
            console.log('Updated user data from status check:', updatedUserData);
              
            // Aktualizuj localStorage
            localStorage.setItem('user', JSON.stringify(updatedUserData));
              
            // Możemy wymusić odświeżenie strony, aby zapewnić aktualizację wszystkich komponentów
            window.location.reload();
          }
        } catch (error) {
          console.error('Error refreshing user data:', error);
        }
      }
    };
    
    checkCurrentUserStatus();
  }, [isAuthenticated, user]);

  const handleLogoutClick = (e) => {
    e.preventDefault();
    setShowLogoutModal(true);
  };

  const handleConfirmLogout = async () => {
    setShowLogoutModal(false);
    setIsLoggingOut(true);

    try {
      await logout();
      addSuccess('Wylogowano pomyślnie.');
      navigate('/login');
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Wystąpił błąd podczas wylogowywania. Spróbuj ponownie później.';
      addError(errorMessage);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleCancelLogout = () => {
    setShowLogoutModal(false);
  };

  return (
    <>
      <nav className="navbar navbar-expand-lg navbar-light bg-light">
        <div className="container">
          <Link className="navbar-brand" to="/">Steambay</Link>
          <button 
            className="navbar-toggler" 
            type="button" 
            data-bs-toggle="collapse" 
            data-bs-target="#navbarNav" 
            aria-controls="navbarNav" 
            aria-expanded="false" 
            aria-label="Toggle navigation"
          >
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0">
              <li className="nav-item">
                <NavLink 
                  className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                  to="/"
                >
                  Strona Główna
                </NavLink>
              </li>
              
              {isAuthenticated && user?.role === 'Buyer' && (
                <>
                  <li className="nav-item">
                    <NavLink 
                      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                      to="/account"
                    >
                      Moje Konto
                    </NavLink>
                  </li>
                  <li className="nav-item">
                    <NavLink 
                      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                      to="/orders"
                    >
                      Moje Zamówienia
                    </NavLink>
                  </li>
                </>
              )}
              
              {isAuthenticated && user?.role === 'Seller' && (
                <>
                  <li className="nav-item">
                    <NavLink 
                      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                      to="/account"
                    >
                      Moje Konto
                    </NavLink>
                  </li>
                  <li className="nav-item">
                    <NavLink 
                      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                      to="/seller/offers"
                    >
                      Moje Oferty
                    </NavLink>
                  </li>
                  <li className="nav-item">
                    <NavLink 
                      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                      to="/seller/sales"
                    >
                      Historia Sprzedaży
                    </NavLink>
                  </li>
                </>
              )}
              
              {isAuthenticated && user?.role === 'Admin' && (
                <>
                  <li className="nav-item">
                    <NavLink 
                      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                      to="/account"
                    >
                      Moje Konto
                    </NavLink>
                  </li>
                  <li className="nav-item">
                    <NavLink 
                      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                      to="/admin"
                    >
                      Panel Admina
                    </NavLink>
                  </li>
                </>
              )}
            </ul>
            
            <ul className="navbar-nav ms-auto">
              {isAuthenticated ? (
                <>
                  {user?.email ? (
                    <li className="nav-item">
                      <span className="nav-link">
                        <i className="bi bi-person-circle me-1"></i>
                        <strong>{user.email}</strong>
                      </span>
                    </li>
                  ) : (
                    <li className="nav-item">
                      <span className="nav-link text-warning">
                        <i className="bi bi-exclamation-triangle me-1"></i>
                        Email not available
                      </span>
                    </li>
                  )}
                  <li className="nav-item">
                    <a
                      href="#"
                      className="nav-link"
                      onClick={handleLogoutClick}
                      aria-label="Wyloguj się z systemu"
                    >
                      {isLoggingOut ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
                          Wylogowywanie...
                        </>
                      ) : (
                        "Wyloguj się"
                      )}
                    </a>
                  </li>
                  {user?.role === 'Buyer' && (
                    <li className="nav-item">
                      <NavLink 
                        className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                        to="/cart"
                        aria-label="Koszyk zakupowy"
                      >
                        <i className="bi bi-cart" aria-hidden="true"></i>
                        {totalItems > 0 && (
                          <span className="badge bg-primary rounded-pill ms-1">{totalItems}</span>
                        )}
                      </NavLink>
                    </li>
                  )}
                </>
              ) : (
                <>
                  <li className="nav-item">
                    <NavLink 
                      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                      to="/login"
                    >
                      Logowanie
                    </NavLink>
                  </li>
                  <li className="nav-item">
                    <NavLink 
                      className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                      to="/register"
                    >
                      Rejestracja
                    </NavLink>
                  </li>
                </>
              )}
            </ul>
          </div>
        </div>
      </nav>

      {/* Logout confirmation modal */}
      <ConfirmLogoutModal
        isOpen={showLogoutModal}
        onConfirm={handleConfirmLogout}
        onCancel={handleCancelLogout}
      />
    </>
  );
};

export default React.memo(Header); 