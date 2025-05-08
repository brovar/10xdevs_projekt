import React, { useState, useEffect, useCallback } from 'react';
import { Container, Row, Col, Alert, Spinner } from 'react-bootstrap';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Components
import UserProfileInfo from '../../components/account/UserProfileInfo';
import UpdateProfileForm from '../../components/account/UpdateProfileForm';
import ChangePasswordForm from '../../components/account/ChangePasswordForm';

// Services
import { fetchAccountDetails, updateAccountDetails, changePassword } from '../../services/accountService';

/**
 * AccountPage - User account management page
 * 
 * This page displays user profile information and allows users to:
 * - View their profile information
 * - Update their first and last name
 * - Change their password
 */
const AccountPage = () => {
  // User data state
  const [userData, setUserData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Form states
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [updateProfileError, setUpdateProfileError] = useState(null);
  
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [changePasswordError, setChangePasswordError] = useState(null);
  const [changePasswordSuccess, setChangePasswordSuccess] = useState(null);

  // Fetch user data
  const fetchUserData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const data = await fetchAccountDetails();
      console.log('Fetched account details:', data);
      
      // Map backend data (snake_case) to frontend model (camelCase)
      const userVM = {
        id: data.id,
        email: data.email,
        role: data.role,
        status: data.status,
        firstName: data.first_name || '',
        lastName: data.last_name || '',
        createdAt: new Date(data.created_at).toLocaleDateString('pl-PL')
      };
      
      setUserData(userVM);
    } catch (error) {
      console.error('Failed to fetch user data:', error);
      setError('Nie udało się załadować danych konta. Spróbuj odświeżyć stronę.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load user data on component mount
  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  // Handle profile update
  const handleUpdateProfile = async (formData) => {
    setIsUpdatingProfile(true);
    setUpdateProfileError(null);
    
    try {
      const updatedData = await updateAccountDetails(formData);
      
      // Map updated data to user view model
      const updatedUserVM = {
        ...userData,
        firstName: updatedData.first_name || '',
        lastName: updatedData.last_name || ''
      };
      
      setUserData(updatedUserVM);
      toast.success('Profil zaktualizowany pomyślnie.');
    } catch (error) {
      console.error('Failed to update profile:', error);
      
      // Extract error message from API response or use a default
      const errorMessage = error.response?.data?.message || 'Nie udało się zaktualizować profilu. Spróbuj ponownie później.';
      setUpdateProfileError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  // Handle password change
  const handleChangePassword = async (formData) => {
    setIsChangingPassword(true);
    setChangePasswordError(null);
    setChangePasswordSuccess(null);
    
    try {
      // Send only current_password and new_password to API
      const passwordData = {
        currentPassword: formData.currentPassword,
        newPassword: formData.newPassword
      };
      
      // Call the API - fixed unused variable
      await changePassword(passwordData);
      
      setChangePasswordSuccess('Hasło zmienione pomyślnie.');
      toast.success('Hasło zmienione pomyślnie.');
    } catch (error) {
      console.error('Failed to change password:', error);
      
      // Extract error message from API response or use a default
      const errorMessage = error.response?.data?.message || 'Nie udało się zmienić hasła. Spróbuj ponownie później.';
      setChangePasswordError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <Container className="py-5">
      <ToastContainer position="top-right" autoClose={5000} />
      
      <h1 className="mb-4">Moje Konto</h1>
      
      {isLoading ? (
        <div className="text-center py-5">
          <Spinner animation="border" role="status" variant="primary">
            <span className="visually-hidden">Ładowanie...</span>
          </Spinner>
          <p className="mt-3">Ładowanie danych konta...</p>
        </div>
      ) : error ? (
        <Alert variant="danger" className="mb-4">
          {error}
        </Alert>
      ) : (
        <Row>
          <Col lg={6}>
            <UserProfileInfo userData={userData} />
            <UpdateProfileForm
              initialData={userData}
              onSubmit={handleUpdateProfile}
              isSubmitting={isUpdatingProfile}
              error={updateProfileError}
            />
          </Col>
          <Col lg={6}>
            <ChangePasswordForm
              onSubmit={handleChangePassword}
              isSubmitting={isChangingPassword}
              error={changePasswordError}
              successMessage={changePasswordSuccess}
            />
          </Col>
        </Row>
      )}
    </Container>
  );
};

export default AccountPage; 