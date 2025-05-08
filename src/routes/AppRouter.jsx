import React, { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { NotificationProvider } from '../contexts/NotificationContext';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';

// Lazy-loaded components
const RegisterPage = lazy(() => import('../pages/auth/RegisterPage'));
const LoginPage = lazy(() => import('../pages/auth/LoginPage'));
const LogoutPage = lazy(() => import('../pages/auth/LogoutPage'));
const HomePage = lazy(() => import('../pages/HomePage'));
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
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return children;
};

// Prevents authenticated users from accessing login/register
const RequireAnon = ({ children }) => {
  const { isAuthenticated } = useAuth();

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
      {
        path: 'logout',
        element: <LogoutPage />
      },
      // Protected routes
      {
        path: 'account',
        element: (
          <RequireAuth>
            <div className="container py-5">
              <h2>Moje Konto</h2>
              <p>Ta strona zostanie zaimplementowana później.</p>
            </div>
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
  return (
    <NotificationProvider>
      <RouterProvider router={router} />
    </NotificationProvider>
  );
};

export default AppRouter; 