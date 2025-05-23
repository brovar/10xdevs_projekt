import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { adminUsersApi } from '../../services/adminService.js';

// Use the real admin service
const adminService = {
  getUserDetails: async (userId) => {
    try {
      return await adminUsersApi.getUserDetails(userId);
    } catch (error) {
      console.error('Error fetching user details:', error);
      throw error;
    }
  },
  
  blockUser: async (userId) => {
    try {
      return await adminUsersApi.blockUser(userId);
    } catch (error) {
      console.error('Error blocking user:', error);
      throw error;
    }
  },
  
  unblockUser: async (userId) => {
    try {
      return await adminUsersApi.unblockUser(userId);
    } catch (error) {
      console.error('Error unblocking user:', error);
      throw error;
    }
  }
};

const StatusBadge = ({ status }) => {
  let badgeClass = 'badge ';
  
  switch (status) {
    case 'Active':
      badgeClass += 'bg-success';
      break;
    case 'Inactive':
      badgeClass += 'bg-warning text-dark';
      break;
    case 'Deleted':
      badgeClass += 'bg-danger';
      break;
    default:
      badgeClass += 'bg-secondary';
  }
  
  return (
    <span className={badgeClass} role="status">
      {status}
    </span>
  );
};

const UserInfoItem = ({ label, value }) => {
  return (
    <div className="mb-3">
      <div className="text-muted small mb-1">{label}</div>
      <div>{value || <em className="text-muted">Not provided</em>}</div>
    </div>
  );
};

const UserDetailsPanel = ({ user }) => {
  const formatDate = (dateString) => {
    if (!dateString) return null;
    
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(date);
  };
  
  return (
    <div className="card">
      <div className="card-header bg-light">
        <h5 className="mb-0">User Information</h5>
      </div>
      <div className="card-body">
        <div className="row">
          <div className="col-md-6">
            <UserInfoItem label="ID" value={user.id} />
            <UserInfoItem label="Email" value={user.email} />
            <UserInfoItem label="First Name" value={user.first_name} />
            <UserInfoItem label="Last Name" value={user.last_name} />
          </div>
          <div className="col-md-6">
            <UserInfoItem label="Role" value={user.role} />
            <UserInfoItem label="Status" value={<StatusBadge status={user.status} />} />
            <UserInfoItem label="Created At" value={formatDate(user.created_at)} />
            <UserInfoItem label="Updated At" value={formatDate(user.updated_at)} />
          </div>
        </div>
      </div>
    </div>
  );
};

const ConfirmationModal = ({ isOpen, title, message, onConfirm, onCancel, confirmButtonText, variant = 'primary', isProcessing = false }) => {
  if (!isOpen) return null;
  
  return (
    <div className="modal fade show" style={{ display: 'block' }} tabIndex="-1" role="dialog" aria-modal="true">
      <div className="modal-dialog modal-dialog-centered">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">{title}</h5>
            <button type="button" className="btn-close" onClick={onCancel} aria-label="Close"></button>
          </div>
          <div className="modal-body">
            <p>{message}</p>
          </div>
          <div className="modal-footer">
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={onCancel}
              disabled={isProcessing}
            >
              Cancel
            </button>
            <button 
              type="button" 
              className={`btn btn-${variant}`} 
              onClick={onConfirm}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Processing...
                </>
              ) : (
                confirmButtonText
              )}
            </button>
          </div>
        </div>
      </div>
      <div className="modal-backdrop fade show"></div>
    </div>
  );
};

const ErrorMessageDisplay = ({ error, className = '', onRetry = null }) => {
  if (!error) return null;
  
  return (
    <div className={`alert alert-danger ${className}`} role="alert">
      <div className="d-flex align-items-center">
        <div className="flex-grow-1">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          {typeof error === 'string' ? error : 'An error occurred while performing the operation.'}
        </div>
        {onRetry && (
          <button 
            className="btn btn-sm btn-outline-danger ms-3" 
            onClick={onRetry}
            aria-label="Try again"
          >
            <i className="bi bi-arrow-clockwise"></i> Retry
          </button>
        )}
      </div>
    </div>
  );
};

const LoadingSpinner = ({ text = 'Loading data...' }) => {
  return (
    <div className="d-flex flex-column align-items-center justify-content-center p-4">
      <div className="spinner-border text-primary mb-2" role="status">
        <span className="visually-hidden">Loading...</span>
      </div>
      {text && <div>{text}</div>}
    </div>
  );
};

const AdminUserDetailPage = () => {
  const { userId } = useParams();
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  
  const fetchUserDetails = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);
    
    try {
      const userData = await adminService.getUserDetails(userId);
      setUser(userData);
    } catch (err) {
      setError(err.message || 'An error occurred while fetching user details.');
      console.error('Error fetching user details:', err);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);
  
  useEffect(() => {
    if (userId) {
      fetchUserDetails();
    } else {
      setError('User ID is required');
      setIsLoading(false);
    }
  }, [userId, fetchUserDetails]);
  
  const handleBlockUser = () => {
    if (!user) return;
    
    setConfirmAction({
      type: 'block',
      message: `Are you sure you want to block user ${user.email}?`
    });
  };
  
  const handleUnblockUser = () => {
    if (!user) return;
    
    setConfirmAction({
      type: 'unblock',
      message: `Are you sure you want to unblock user ${user.email}?`
    });
  };
  
  const handleConfirmAction = async () => {
    if (!confirmAction || !userId) return;
    
    setIsProcessing(true);
    setSuccessMessage(null);
    
    try {
      let updatedUser;
      
      if (confirmAction.type === 'block') {
        updatedUser = await adminService.blockUser(userId);
        setSuccessMessage(`User ${user.email} has been blocked.`);
      } else if (confirmAction.type === 'unblock') {
        updatedUser = await adminService.unblockUser(userId);
        setSuccessMessage(`User ${user.email} has been unblocked.`);
      }
      
      if (updatedUser) {
        setUser(updatedUser);
      }
      
      setConfirmAction(null);
    } catch (err) {
      setError(err.message || `An error occurred while ${confirmAction.type === 'block' ? 'blocking' : 'unblocking'} user.`);
      console.error('Error processing action:', err);
    } finally {
      setIsProcessing(false);
    }
  };
  
  return (
    <div className="container py-4">
      <div className="row mb-4">
        <div className="col">
          <Link to="/admin?tab=users" className="btn btn-outline-secondary mb-3">
            <i className="bi bi-arrow-left"></i> Return to Users List
          </Link>
          <h1>User Details</h1>
          {userId && <p className="text-muted">ID: {userId}</p>}
        </div>
      </div>
      
      {/* Success message */}
      {successMessage && (
        <div className="alert alert-success mb-4" role="alert">
          <i className="bi bi-check-circle-fill me-2"></i>
          {successMessage}
        </div>
      )}
      
      {/* Error message */}
      {error && !isLoading && (
        <ErrorMessageDisplay 
          error={error} 
          className="mb-4" 
          onRetry={fetchUserDetails} 
        />
      )}
      
      {/* Loading state */}
      {isLoading && <LoadingSpinner text="Loading user details..." />}
      
      {/* User details */}
      {!isLoading && !error && user && (
        <div className="row">
          <div className="col-12 mb-4">
            <UserDetailsPanel user={user} />
          </div>
          
          {/* User actions */}
          <div className="col-12">
            <div className="card">
              <div className="card-header bg-light">
                <h5 className="mb-0">Actions</h5>
              </div>
              <div className="card-body">
                <div className="d-flex gap-2">
                  {user.status === 'Active' && (
                    <button 
                      className="btn btn-warning" 
                      onClick={handleBlockUser}
                    >
                      <i className="bi bi-lock me-1"></i> Block User
                    </button>
                  )}
                  
                  {user.status === 'Inactive' && (
                    <button 
                      className="btn btn-success" 
                      onClick={handleUnblockUser}
                    >
                      <i className="bi bi-unlock me-1"></i> Unblock User
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Confirmation Modal */}
      <ConfirmationModal 
        isOpen={confirmAction !== null}
        title={confirmAction?.type === 'block' ? 'Block User' : 'Unblock User'}
        message={confirmAction?.message || ''}
        onConfirm={handleConfirmAction}
        onCancel={() => setConfirmAction(null)}
        confirmButtonText={confirmAction?.type === 'block' ? 'Block' : 'Unblock'}
        variant={confirmAction?.type === 'block' ? 'warning' : 'success'}
        isProcessing={isProcessing}
      />
    </div>
  );
};

export default AdminUserDetailPage; 