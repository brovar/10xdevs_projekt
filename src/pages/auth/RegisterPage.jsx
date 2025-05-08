import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import RegistrationForm from '../../components/auth/RegistrationForm';
import { registerUser } from '../../services/authService';
import { useNotifications } from '../../contexts/NotificationContext';

const RegisterPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState(null);
  const navigate = useNavigate();
  const { addSuccess, addError } = useNotifications();

  const handleRegisterSubmit = async (data) => {
    setIsLoading(true);
    setApiError(null);
    
    try {
      const response = await registerUser(data);
      addSuccess('Rejestracja zakończona pomyślnie. Możesz się teraz zalogować.');
      navigate('/login');
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Wystąpił błąd podczas rejestracji. Spróbuj ponownie później.';
      const errorCode = error.response?.data?.error_code;
      
      setApiError(errorMessage);
      addError(errorMessage);
      
      // Handle field-specific errors if needed
      // This would be passed to the form if we needed to display errors at specific fields
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
              <h2 className="text-center">Rejestracja</h2>
            </div>
            <div className="card-body">
              {apiError && (
                <div className="alert alert-danger" role="alert">
                  {apiError}
                </div>
              )}
              <RegistrationForm 
                onSubmit={handleRegisterSubmit} 
                isLoading={isLoading} 
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage; 