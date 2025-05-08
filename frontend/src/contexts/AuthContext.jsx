import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import axios from '../services/api';
import { loginUser, logoutUser } from '../services/authService';

// Tworzenie kontekstu
const AuthContext = createContext();

// Hook użytkowy
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Dostawca kontekstu
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sprawdzenie czy użytkownik jest zalogowany przy ładowaniu strony
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
            const userData = response.data.user;
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
          const parsedUser = JSON.parse(storedUser);
          console.log('Loaded user from localStorage:', parsedUser);
          setUser(parsedUser);
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

  // Funkcja logowania
  const login = useCallback(async (email, password) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await loginUser({ email, password });
      console.log('Login response:', response);
      
      // Make sure user data has an email field
      const userData = {
        ...response,
        email: response.email || email // Use the email from response if available, otherwise use the login email
      };
      
      console.log('User data being saved:', userData);
      
      // Zapisujemy użytkownika w stanie i localStorage
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      
      return userData;
    } catch (error) {
      console.error('Login error:', error);
      const errorMessage = error.response?.data?.message || 'Failed to login';
      setError(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Funkcja czyszczenia wszystkich stanów powiązanych z sesją
  const clearSessionData = useCallback(() => {
    // Czyszczenie localStorage
    localStorage.removeItem('user');
    
    // Wywołane przez inne konteksty - obsługiwane przez event
    const logoutEvent = new CustomEvent('user-logout');
    window.dispatchEvent(logoutEvent);
    
    // Czyszczenie stanu auth
    setUser(null);
    setError(null);
  }, []);

  // Funkcja wylogowania
  const logout = useCallback(async () => {
    setIsLoading(true);
    
    try {
      // Wywołanie API wylogowania
      const response = await logoutUser();
      
      // Czyszczenie wszystkich danych sesji
      clearSessionData();
      
      return response;
    } catch (error) {
      // Jeśli błąd to 401 (Unauthorized), oznacza to, że sesja już wygasła
      // Mimo to czyścimy dane sesji lokalnie
      if (error.response && error.response.status === 401) {
        clearSessionData();
      }
      
      console.error('Error during logout:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [clearSessionData]);

  // Obsługa wygaśnięcia sesji - dodanie globalnego interceptora dla axios
  useEffect(() => {
    // Dodajemy interceptor do obsługi odpowiedzi
    const interceptorId = axios.interceptors.response.use(
      response => response, 
      error => {
        // Jeśli serwer zwraca 401 Unauthorized, a użytkownik jest zalogowany
        // automatycznie wylogowujemy go (sesja wygasła)
        if (error.response && error.response.status === 401 && user) {
          console.warn('Received 401 while user is logged in - clearing session');
          clearSessionData();
        }
        return Promise.reject(error);
      }
    );
    
    // Usuwamy interceptor przy odmontowaniu
    return () => {
      axios.interceptors.response.eject(interceptorId);
    };
  }, [user, clearSessionData]);

  // Log when user state changes
  useEffect(() => {
    console.log('User state changed:', user);
  }, [user]);

  // Wartość kontekstu
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