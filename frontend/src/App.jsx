import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { CartProvider } from './contexts/CartContext';
import { NotificationProvider } from './contexts/NotificationContext';
import AppRouter from './routes/AppRouter';
import './index.css';

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <NotificationProvider>
          <AppRouter />
        </NotificationProvider>
      </CartProvider>
    </AuthProvider>
  );
}

export default App; 