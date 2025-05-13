import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import ProtectedRoute from '../components/shared/ProtectedRoute';

// Lazy load admin components for code splitting
const AdminDashboardPage = React.lazy(() => import('../components/admin/AdminDashboardPage'));
const AdminUserDetailPage = React.lazy(() => import('../components/admin/AdminUserDetailPage'));
const AdminOrderDetailPage = React.lazy(() => import('../components/admin/AdminOrderDetailPage'));

// Loading fallback component
const LoadingFallback = () => <div className="p-4 text-center">Loading...</div>;

const router = createBrowserRouter([
  // Other routes would go here
  
  // Admin routes
  {
    path: '/admin',
    element: <ProtectedRoute role="Admin" />,
    children: [
      {
        index: true,
        element: (
          <React.Suspense fallback={<LoadingFallback />}>
            <AdminDashboardPage />
          </React.Suspense>
        ),
      },
      {
        path: 'users/:userId',
        element: (
          <React.Suspense fallback={<LoadingFallback />}>
            <AdminUserDetailPage />
          </React.Suspense>
        ),
      },
      {
        path: 'orders/:orderId',
        element: (
          <React.Suspense fallback={<LoadingFallback />}>
            <AdminOrderDetailPage />
          </React.Suspense>
        ),
      },
    ],
  },
]);

const Routes: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default Routes; 