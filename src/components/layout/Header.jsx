import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useCart } from '../../contexts/CartContext';

const Header = () => {
  const { isAuthenticated, user } = useAuth();
  const { totalItems } = useCart();

  return (
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
                <li className="nav-item">
                  <NavLink 
                    className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} 
                    to="/logout"
                    aria-label="Wyloguj się z systemu"
                  >
                    Wyloguj się
                  </NavLink>
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
  );
};

export default React.memo(Header); 