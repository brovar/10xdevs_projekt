import React from 'react';
import { createRoot } from 'react-dom/client';
import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import 'bootstrap-icons/font/bootstrap-icons.css';
import AppRouter from './routes/AppRouter';
import { AuthProvider } from './contexts/AuthContext';
import { CartProvider } from './contexts/CartContext';
import './index.css';

// Inicjalizacja aplikacji
const root = createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <AuthProvider>
      <CartProvider>
        <AppRouter />
      </CartProvider>
    </AuthProvider>
  </React.StrictMode>
); 