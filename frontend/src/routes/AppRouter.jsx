import React, { lazy, Suspense, useEffect } from 'react';
import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';

// Lazy-loaded components
const RegisterPage = lazy(() => import('../pages/auth/RegisterPage'));
const LoginPage = lazy(() => import('../pages/auth/LoginPage'));
const HomePage = lazy(() => import('../pages/HomePage'));
const AccountPage = lazy(() => import('../pages/account/AccountPage'));
const OrdersPage = lazy(() => import('../pages/account/OrdersPage'));
// Pozostałe strony będą dodawane tutaj

// Layout component
const AppLayout = () => {
  return (
    <div className="d-flex flex-column min-vh-100">
      <Header />
      <main className="flex-grow-1">
        <Suspense fallback={<div className="container py-5 text-center">Ładowanie...</div>}>
          <Outlet />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
};

// Auth guard component
const RequireAuth = ({ children, requiredRole = null }) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  
  // Debug logging
  useEffect(() => {
    console.log('RequireAuth - Auth status:', { 
      isAuthenticated, 
      user, 
      isLoading, 
      role: user?.role,
      requiredRole
    });
  }, [isAuthenticated, user, isLoading, requiredRole]);

  // While still checking authentication status, show loading
  if (isLoading) {
    return (
      <div className="container py-5 text-center">
        <p>Weryfikacja sesji użytkownika...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    console.log('User is not authenticated, redirecting to login');
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    console.log(`User role ${user?.role} doesn't match required role ${requiredRole}, redirecting to home`);
    return <Navigate to="/" replace />;
  }

  console.log('Authentication check passed, rendering protected content');
  return children;
};

// Prevents authenticated users from accessing login/register
const RequireAnon = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  // While still checking authentication status, show loading
  if (isLoading) {
    return (
      <div className="container py-5 text-center">
        <p>Weryfikacja sesji użytkownika...</p>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
};

// Loader komponentu - opcjonalnie do wykorzystania zgodnie z React Router
const registerLoader = () => {
  return null; // Tu potencjalnie możemy pobierać dane do inicjalizacji
};

// Routing configuration
const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <HomePage />
      },
      {
        path: 'register',
        element: (
          <RequireAnon>
            <RegisterPage />
          </RequireAnon>
        )
      },
      {
        path: 'login',
        element: (
          <RequireAnon>
            <LoginPage />
          </RequireAnon>
        )
      },
      // Protected routes
      {
        path: 'account',
        element: (
          <RequireAuth>
            <AccountPage />
          </RequireAuth>
        )
      },
      {
        path: 'orders',
        element: (
          <RequireAuth requiredRole="Buyer">
            <OrdersPage />
          </RequireAuth>
        )
      },
      {
        path: 'cart',
        element: (
          <RequireAuth requiredRole="Buyer">
            <div className="container py-5">
              <h2>Koszyk</h2>
              <p>Ta strona zostanie zaimplementowana później.</p>
            </div>
          </RequireAuth>
        )
      },
      // 404 route
      {
        path: '*',
        element: (
          <div className="container py-5 text-center">
            <h2>404 - Strona nie znaleziona</h2>
            <p>Przepraszamy, ale strona, której szukasz, nie istnieje.</p>
          </div>
        )
      }
    ]
  }
]);

const AppRouter = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter; 