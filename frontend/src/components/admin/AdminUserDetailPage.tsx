import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { adminUsersApi } from '../../services/adminService.ts';
import { UserDTO } from '../../types/api.ts';
import UserDetailsPanel from './UserDetailsPanel.tsx';
import LoadingSpinner from '../shared/LoadingSpinner.tsx';
import ErrorMessageDisplay from '../shared/ErrorMessageDisplay.tsx';

const AdminUserDetailPage: React.FC = () => {
  const { userId } = useParams<{ userId: string }>();
  const [user, setUser] = useState<UserDTO | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) {
      setError('ID użytkownika jest wymagane');
      return;
    }

    const fetchUser = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const userData = await adminUsersApi.getUserDetails(userId);
        setUser(userData);
      } catch (err) {
        const errorMessage = err instanceof Error 
          ? err.message 
          : 'Wystąpił błąd podczas pobierania danych użytkownika';
        setError(errorMessage);
        console.error('Error fetching user details:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUser();
  }, [userId]);

  return (
    <div className="container py-4">
      <div className="row mb-4">
        <div className="col">
          <Link to="/admin?tab=users" className="btn btn-outline-secondary mb-3">
            &laquo; Powrót do listy użytkowników
          </Link>
          <h1>Szczegóły Użytkownika</h1>
          {userId && <p className="text-muted">ID: {userId}</p>}
        </div>
      </div>

      {/* Loading state */}
      {isLoading && <LoadingSpinner text="Ładowanie szczegółów użytkownika..." />}
      
      {/* Error state */}
      {error && !isLoading && (
        <ErrorMessageDisplay error={error} className="mb-4" />
      )}
      
      {/* User details */}
      {!isLoading && !error && user && (
        <UserDetailsPanel user={user} />
      )}
    </div>
  );
};

export default AdminUserDetailPage; 