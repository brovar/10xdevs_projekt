import React, { lazy, Suspense, useEffect } from 'react';
import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';
import ErrorBoundary from '../components/common/ErrorBoundary';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorPage from '../pages/ErrorPage';

// Lazy-loaded components
const RegisterPage = lazy(() => import('../pages/auth/RegisterPage'));
const LoginPage = lazy(() => import('../pages/auth/LoginPage'));
const OfferDiscoveryPage = lazy(() => import('../pages/offers/OfferDiscoveryPage'));
const OfferDetailPage = lazy(() => import('../pages/offers/OfferDetailPage'));
const AccountPage = lazy(() => import('../pages/account/AccountPage'));
const OrdersPage = lazy(() => import('../pages/account/OrdersPage'));
const OrderDetailPage = lazy(() => import('../pages/orders/OrderDetailPage'));
// Seller pages
const MyOffersPage = lazy(() => import('../pages/seller/MyOffersPage'));
// Poprawny import dla historii sprzedaży, używając pełnej implementacji, która już istnieje
const SalesHistoryPage = lazy(() => import('../pages/seller/SellerSalesHistoryPage'));
const CreateOfferPage = lazy(() => import('../pages/seller/CreateOfferPage'));
// Pozostałe strony będą dodawane tutaj

// Layout component
const AppLayout = () => {
  return (
    <div className="d-flex flex-column min-vh-100">
      <Header />
      <main className="flex-grow-1">
        <Suspense fallback={<LoadingSpinner message="Ładowanie zawartości..." />}>
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

// Routing configuration
const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<LoadingSpinner message="Ładowanie strony głównej..." />}>
            <OfferDiscoveryPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />
      },
      {
        path: 'offers',
        element: (
          <Suspense fallback={<LoadingSpinner message="Ładowanie ofert..." />}>
            <OfferDiscoveryPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />
      },
      {
        path: 'offers/:offerId',
        element: (
          <Suspense fallback={<LoadingSpinner message="Ładowanie szczegółów oferty..." />}>
            <OfferDetailPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />
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
        path: 'orders/:orderId',
        element: (
          <RequireAuth requiredRole="Buyer">
            <OrderDetailPage />
          </RequireAuth>
        )
      },
      {
        path: 'cart',
        element: (
          <div className="container py-5">
            <h2>Koszyk</h2>
            <p>Ta strona zostanie zaimplementowana później.</p>
          </div>
        )
      },
      // Seller routes
      {
        path: 'seller/offers',
        element: (
          <RequireAuth requiredRole="Seller">
            <Suspense fallback={<LoadingSpinner message="Ładowanie ofert..." />}>
              <MyOffersPage />
            </Suspense>
          </RequireAuth>
        ),
        errorElement: <ErrorBoundary />
      },
      {
        path: 'seller/offers/create',
        element: (
          <RequireAuth requiredRole="Seller">
            <Suspense fallback={<LoadingSpinner message="Ładowanie formularza..." />}>
              <CreateOfferPage />
            </Suspense>
          </RequireAuth>
        ),
        errorElement: <ErrorBoundary />
      },
      {
        path: 'seller/sales',
        element: (
          <RequireAuth requiredRole="Seller">
            <Suspense fallback={<LoadingSpinner message="Ładowanie historii sprzedaży..." />}>
              <SalesHistoryPage />
            </Suspense>
          </RequireAuth>
        ),
        errorElement: <ErrorBoundary />
      },
      {
        path: '*',
        element: <ErrorPage />
      }
    ]
  }
]);

const AppRouter = () => {
  return <RouterProvider router={router} />;
};

export default AppRouter;