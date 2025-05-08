import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../../components/auth/LoginForm';
import { useAuth } from '../../contexts/AuthContext';
import { useNotifications } from '../../contexts/NotificationContext';

const LoginPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const navigate = useNavigate();
  const { login } = useAuth();
  const { addSuccess, addError } = useNotifications();

  const handleLoginSubmit = async (credentials) => {
    setIsLoading(true);
    setApiError(null);
    
    try {
      await login(credentials.email, credentials.password);
      addSuccess('Logowanie zakończone pomyślnie.');
      navigate('/');
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Wystąpił błąd podczas logowania. Spróbuj ponownie później.';
      const errorCode = error.response?.data?.error_code;
      
      setApiError(errorMessage);
      addError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mt-5">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card">
            <div className="card-header">
              <h2 className="text-center">Logowanie</h2>
            </div>
            <div className="card-body">
              {apiError && (
                <div className="alert alert-danger" role="alert">
                  {apiError}
                </div>
              )}
              <LoginForm 
                onSubmit={handleLoginSubmit} 
                isLoading={isLoading} 
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage; 