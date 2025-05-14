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
// Correct import for sales history, using the full implementation that already exists
const SalesHistoryPage = lazy(() => import('../pages/seller/SellerSalesHistoryPage'));
const CreateOfferPage = lazy(() => import('../pages/seller/CreateOfferPage'));
// Admin pages
const AdminDashboardPage = lazy(() => import('../pages/admin/AdminDashboardPage'));
const AdminUserDetailPage = lazy(() => import('../pages/admin/AdminUserDetailPage'));
const AdminOrderDetailPage = lazy(() => import('../pages/admin/AdminOrderDetailPage'));
// Other pages will be added here

// Layout component
const AppLayout = () => {
  return (
    <div className="d-flex flex-column min-vh-100">
      <Header />
      <main className="flex-grow-1">
        <Suspense fallback={<LoadingSpinner message="Loading content..." />}>
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
        <p>Verifying user session...</p>
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
        <p>Verifying user session...</p>
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
          <Suspense fallback={<LoadingSpinner message="Loading home page..." />}>
            <OfferDiscoveryPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />
      },
      {
        path: 'offers',
        element: (
          <Suspense fallback={<LoadingSpinner message="Loading offers..." />}>
            <OfferDiscoveryPage />
          </Suspense>
        ),
        errorElement: <ErrorBoundary />
      },
      {
        path: 'offers/:offerId',
        element: (
          <Suspense fallback={<LoadingSpinner message="Loading offer details..." />}>
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
            <h2>Cart</h2>
            <p>This page will be implemented later.</p>
          </div>
        )
      },
      // Seller routes
      {
        path: 'seller/offers',
        element: (
          <RequireAuth requiredRole="Seller">
            <Suspense fallback={<LoadingSpinner message="Loading offers..." />}>
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
            <Suspense fallback={<LoadingSpinner message="Loading form..." />}>
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
            <Suspense fallback={<LoadingSpinner message="Loading sales history..." />}>
              <SalesHistoryPage />
            </Suspense>
          </RequireAuth>
        ),
        errorElement: <ErrorBoundary />
      },
      // Admin routes
      {
        path: 'admin',
        element: (
          <RequireAuth requiredRole="Admin">
            <Suspense fallback={<LoadingSpinner message="Loading admin panel..." />}>
              <AdminDashboardPage />
            </Suspense>
          </RequireAuth>
        ),
        errorElement: <ErrorBoundary />
      },
      {
        path: 'admin/users/:userId',
        element: (
          <RequireAuth requiredRole="Admin">
            <Suspense fallback={<LoadingSpinner message="Loading user details..." />}>
              <AdminUserDetailPage />
            </Suspense>
          </RequireAuth>
        ),
        errorElement: <ErrorBoundary />
      },
      {
        path: 'admin/orders/:orderId',
        element: (
          <RequireAuth requiredRole="Admin">
            <Suspense fallback={<LoadingSpinner message="Loading order details..." />}>
              <AdminOrderDetailPage />
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