import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import axios from '../services/api';
import { loginUser, logoutUser } from '../services/authService';

// Create context
const AuthContext = createContext();

// Utility hook
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Helper function to normalize user data and ensure consistent ID fields
const normalizeUserData = (userData) => {
  if (!userData) return null;
  
  // Ensure the user has a role
  const role = userData.role || (userData.user?.role) || 'Buyer';
  
  // Ensure both id and user_id are present
  const userId = userData.id || userData.user_id;
  
  return {
    ...userData,
    role,
    id: userId,
    user_id: userId
  };
};

// Context provider
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is logged in when page loads
  useEffect(() => {
    const checkAuthStatus = async () => {
      try {
        console.log('Checking auth status...');
        
        // Try to get user session from the backend first
        try {
          const response = await axios.get('/auth/status');
          console.log('Auth status response:', response.data);
          if (response.data && response.data.is_authenticated) {
            console.log('User is authenticated according to backend');
            const userData = normalizeUserData(response.data.user);
            setUser(userData);
            
            // Update localStorage to keep it in sync
            localStorage.setItem('user', JSON.stringify(userData));
            setIsLoading(false);
            return;
          }
        } catch (apiError) {
          console.log('Could not verify auth with backend, falling back to localStorage:', apiError);
        }
        
        // Fallback to localStorage if API verification fails
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          try {
            const parsedUser = JSON.parse(storedUser);
            console.log('Loaded user from localStorage:', parsedUser);
            
            const normalizedUser = normalizeUserData(parsedUser);
            setUser(normalizedUser);
            
            // Update localStorage with the normalized user data
            localStorage.setItem('user', JSON.stringify(normalizedUser));
          } catch (parseError) {
            console.error('Error parsing user from localStorage:', parseError);
            localStorage.removeItem('user'); // Remove invalid data
          }
        }
      } catch (error) {
        console.error('Error checking auth status:', error);
        setError('Failed to authenticate');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  // Login function
  const login = useCallback(async (email, password) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // 1. Execute login request
      const response = await loginUser({ email, password });
      console.log('Login response:', response);
      
      // 2. Immediately fetch complete user data from status endpoint
      const statusResponse = await axios.get('/auth/status');
      console.log('Auth status after login:', statusResponse.data);
      
      if (statusResponse.data && statusResponse.data.is_authenticated) {
        // Use user data from status response
        const userData = normalizeUserData(statusResponse.data.user);
        
        console.log('User data being saved:', userData);
        
        // Save user in state and localStorage
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
        
        return userData;
      } else {
        // Fallback to previous logic
        const userData = normalizeUserData({
          ...response,
          email: response.email || email
        });
        
        console.log('Fallback user data being saved:', userData);
        
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
        
        return userData;
      }
    } catch (error) {
      console.error('Login error:', error);
      const errorMessage = error.response?.data?.message || 'Failed to login';
      setError(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Function to clear all session-related states
  const clearSessionData = useCallback(() => {
    // Clear localStorage
    localStorage.removeItem('user');
    
    // Called by other contexts - handled by event
    const logoutEvent = new CustomEvent('user-logout');
    window.dispatchEvent(logoutEvent);
    
    // Clear auth state
    setUser(null);
    setError(null);
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    setIsLoading(true);
    
    try {
      // Call logout API
      const response = await logoutUser();
      
      // Clear all session data
      clearSessionData();
      
      return response;
    } catch (error) {
      // If error is 401 (Unauthorized), it means the session already expired
      // We still clear session data locally
      if (error.response && error.response.status === 401) {
        clearSessionData();
      }
      
      console.error('Error during logout:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [clearSessionData]);

  // Handle session expiration - add global interceptor for axios
  useEffect(() => {
    // Add interceptor to handle responses
    const interceptorId = axios.interceptors.response.use(
      response => response, 
      error => {
        // If server returns 401 Unauthorized and user is logged in
        // automatically log them out (session expired)
        if (error.response && error.response.status === 401 && user) {
          console.warn('Received 401 while user is logged in - clearing session');
          clearSessionData();
        }
        return Promise.reject(error);
      }
    );
    
    // Remove interceptor on unmount
    return () => {
      axios.interceptors.response.eject(interceptorId);
    };
  }, [user, clearSessionData]);

  // Log when user state changes
  useEffect(() => {
    console.log('User state changed:', user);
  }, [user]);

  // Context value
  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    logout,
    clearSessionData
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired
};

export default AuthContext; 