import React, { useState, useEffect } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { UserRole } from '../../types/api';
import LoadingSpinner from './LoadingSpinner';

// This would normally come from an auth context/provider
// For now, we'll mock it for development purposes
const useAuth = () => {
  // Mock auth - in a real app, this would check the user's session/token
  return {
    isAuthenticated: true,
    user: {
      role: 'Admin' // Mocking an admin user for development
    }
  };
};

interface ProtectedRouteProps {
  role?: UserRole;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ role }) => {
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);
  const location = useLocation();

  useEffect(() => {
    // This would typically fetch the current user data from an API or context
    // For demo purposes, we'll simulate an API call
    const checkAuthorization = async () => {
      try {
        // In a real app, you would fetch the user data from an API or context
        // For demo, let's assume the user is logged in as Admin
        const mockUser = { role: UserRole.ADMIN };
        
        // Check if the user has the required role
        const authorized = !role || mockUser.role === role;
        setIsAuthorized(authorized);
      } catch (error) {
        console.error('Error checking authorization:', error);
        setIsAuthorized(false);
      }
    };

    checkAuthorization();
  }, [role]);

  // If still checking authorization, show loading spinner
  if (isAuthorized === null) {
    return <LoadingSpinner text="Checking authorization..." />;
  }

  // If not authorized, redirect to login
  if (!isAuthorized) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // If authorized, render the child routes
  return <Outlet />;
};

export default ProtectedRoute; 