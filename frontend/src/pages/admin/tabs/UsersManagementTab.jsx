import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { adminUsersApi } from '../../../services/adminService.js';

// Use the real admin service
const adminService = {
  getUsers: async (params = {}) => {
    try {
      return await adminUsersApi.getUsers(params);
    } catch (error) {
      console.error('Error fetching users:', error);
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

const UserFiltersComponent = ({ filters, onFilterChange }) => {
  const [localFilters, setLocalFilters] = useState(filters);
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLocalFilters(prev => ({ ...prev, [name]: value }));
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onFilterChange(localFilters);
  };
  
  const handleReset = () => {
    const resetFilters = {
      page: 1,
      limit: 10,
      search: '',
      role: '',
      status: ''
    };
    setLocalFilters(resetFilters);
    onFilterChange(resetFilters);
  };
  
  return (
    <div className="card mb-4">
      <div className="card-header bg-light">
        <h5 className="mb-0">Filters</h5>
      </div>
      <div className="card-body">
        <form onSubmit={handleSubmit}>
          <div className="row g-3">
            <div className="col-md-4">
              <label htmlFor="search" className="form-label">Search</label>
              <input
                type="text"
                className="form-control"
                id="search"
                name="search"
                placeholder="Email, first name or last name"
                value={localFilters.search || ''}
                onChange={handleInputChange}
              />
            </div>
            
            <div className="col-md-3">
              <label htmlFor="role" className="form-label">Role</label>
              <select
                className="form-select"
                id="role"
                name="role"
                value={localFilters.role || ''}
                onChange={handleInputChange}
              >
                <option value="">All roles</option>
                <option value="Buyer">Buyer</option>
                <option value="Seller">Seller</option>
                <option value="Admin">Administrator</option>
              </select>
            </div>
            
            <div className="col-md-3">
              <label htmlFor="status" className="form-label">Status</label>
              <select
                className="form-select"
                id="status"
                name="status"
                value={localFilters.status || ''}
                onChange={handleInputChange}
              >
                <option value="">All statuses</option>
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
                <option value="Deleted">Deleted</option>
              </select>
            </div>
            
            <div className="col-md-2 d-flex align-items-end">
              <div className="d-grid gap-2 w-100">
                <button type="submit" className="btn btn-primary">
                  <i className="bi bi-search"></i> Filter
                </button>
                <button type="button" className="btn btn-outline-secondary" onClick={handleReset}>
                  Reset
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
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

const UserActionsComponent = ({ user, onBlock, onUnblock }) => {
  return (
    <div className="d-flex gap-2">
      <Link to={`/admin/users/${user.id}`} className="btn btn-sm btn-outline-primary">
        <i className="bi bi-info-circle"></i> Details
      </Link>
      
      {user.status === 'Active' && (
        <button 
          className="btn btn-sm btn-warning" 
          onClick={() => onBlock(user.id)}
          aria-label={`Block user ${user.email}`}
        >
          <i className="bi bi-lock"></i> Block
        </button>
      )}
      
      {user.status === 'Inactive' && (
        <button 
          className="btn btn-sm btn-success" 
          onClick={() => onUnblock(user.id)}
          aria-label={`Unblock user ${user.email}`}
        >
          <i className="bi bi-unlock"></i> Unblock
        </button>
      )}
    </div>
  );
};

const UserListTable = ({ users, onBlock, onUnblock }) => {
  if (!users || users.length === 0) {
    return (
      <div className="alert alert-info" role="alert">
        No users matching search criteria found.
      </div>
    );
  }
  
  const formatDate = (dateString) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };
  
  return (
    <div className="table-responsive">
      <table className="table table-striped table-hover">
        <thead className="table-light">
          <tr>
            <th scope="col">Email</th>
            <th scope="col">Full Name</th>
            <th scope="col">Role</th>
            <th scope="col">Status</th>
            <th scope="col">Created At</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id}>
              <td>{user.email}</td>
              <td>
                {user.first_name && user.last_name
                  ? `${user.first_name} ${user.last_name}`
                  : user.first_name || user.last_name || '-'}
              </td>
              <td>{user.role}</td>
              <td>
                <StatusBadge status={user.status} />
              </td>
              <td>{formatDate(user.created_at)}</td>
              <td>
                <UserActionsComponent 
                  user={user} 
                  onBlock={onBlock} 
                  onUnblock={onUnblock} 
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const PaginationComponent = ({ paginationInfo, onPageChange }) => {
  const { currentPage, totalPages } = paginationInfo;
  
  if (totalPages <= 1) {
    return null;
  }
  
  // Generate page numbers array
  const getPageNumbers = () => {
    const pageNumbers = [];
    
    // Always include first page
    pageNumbers.push(1);
    
    // Calculate range around current page
    let startPage = Math.max(2, currentPage - 1);
    let endPage = Math.min(totalPages - 1, currentPage + 1);
    
    // Add ellipsis after first page if needed
    if (startPage > 2) {
      pageNumbers.push('...');
    }
    
    // Add pages around current page
    for (let i = startPage; i <= endPage; i++) {
      pageNumbers.push(i);
    }
    
    // Add ellipsis before last page if needed
    if (endPage < totalPages - 1) {
      pageNumbers.push('...');
    }
    
    // Always include last page if not already included
    if (totalPages > 1) {
      pageNumbers.push(totalPages);
    }
    
    return pageNumbers;
  };
  
  const pages = getPageNumbers();
  
  return (
    <nav aria-label="User pagination navigation">
      <ul className="pagination justify-content-center">
        <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
          <button 
            className="page-link" 
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            aria-label="Previous page"
          >
            &laquo; Previous
          </button>
        </li>
        
        {pages.map((page, index) => (
          <li 
            key={index} 
            className={`page-item ${page === currentPage ? 'active' : ''} ${page === '...' ? 'disabled' : ''}`}
          >
            <button 
              className="page-link" 
              onClick={() => page !== '...' ? onPageChange(page) : null}
              aria-current={page === currentPage ? 'page' : undefined}
            >
              {page}
            </button>
          </li>
        ))}
        
        <li className={`page-item ${currentPage === totalPages ? 'disabled' : ''}`}>
          <button 
            className="page-link" 
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            aria-label="Next page"
          >
            Next &raquo;
          </button>
        </li>
      </ul>
      <div className="text-center text-muted small">
        Showing page {currentPage} of {totalPages}
      </div>
    </nav>
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
          {typeof error === 'string' ? error : 'An error occurred during the operation.'}
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

const UsersManagementTab = () => {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [paginationInfo, setPaginationInfo] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    limit: 10
  });
  
  // Filters state
  const [filters, setFilters] = useState({
    page: 1,
    limit: 10,
    search: '',
    role: '',
    status: ''
  });
  
  // Confirmation modal state
  const [confirmAction, setConfirmAction] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Fetch users based on current filters
  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await adminService.getUsers(filters);
      setUsers(response.items);
      setPaginationInfo({
        currentPage: response.page,
        totalPages: response.pages,
        totalItems: response.total,
        limit: response.limit
      });
    } catch (err) {
      setError(err.message || 'An error occurred while fetching the users list.');
      console.error('Error fetching users:', err);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);
  
  // Initial fetch
  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);
  
  // Handle filter changes
  const handleFilterChange = (newFilters) => {
    setFilters({
      ...filters,
      ...newFilters,
      page: 1 // Reset to first page when filters change
    });
  };
  
  // Handle page change
  const handlePageChange = (page) => {
    setFilters({
      ...filters,
      page
    });
  };
  
  // Handle block user action
  const handleBlockUser = (userId) => {
    const user = users.find(u => u.id === userId);
    if (!user) return;
    
    setConfirmAction({
      type: 'block',
      userId,
      message: `Are you sure you want to block user ${user.email}?`
    });
  };
  
  // Handle unblock user action
  const handleUnblockUser = (userId) => {
    const user = users.find(u => u.id === userId);
    if (!user) return;
    
    setConfirmAction({
      type: 'unblock',
      userId,
      message: `Are you sure you want to unblock user ${user.email}?`
    });
  };
  
  // Handle confirmation modal actions
  const handleConfirmAction = async () => {
    if (!confirmAction) return;
    
    setIsProcessing(true);
    
    try {
      if (confirmAction.type === 'block') {
        await adminService.blockUser(confirmAction.userId);
      } else if (confirmAction.type === 'unblock') {
        await adminService.unblockUser(confirmAction.userId);
      }
      
      // Refresh user list after successful action
      await fetchUsers();
      
      // Close modal
      setConfirmAction(null);
    } catch (err) {
      setError(err.message || `An error occurred while ${confirmAction.type === 'block' ? 'blocking' : 'unblocking'} the user.`);
      console.error('Error processing action:', err);
    } finally {
      setIsProcessing(false);
    }
  };
  
  return (
    <div className="users-management-tab">
      <h2 className="mb-4">User Management</h2>
      
      {/* Filters */}
      <UserFiltersComponent 
        filters={filters}
        onFilterChange={handleFilterChange}
      />
      
      {/* Error message */}
      {error && !isLoading && (
        <ErrorMessageDisplay 
          error={error} 
          className="mb-4" 
          onRetry={fetchUsers} 
        />
      )}
      
      {/* Loading state */}
      {isLoading && <LoadingSpinner text="Loading users..." />}
      
      {/* Users table */}
      {!isLoading && !error && (
        <>
          <UserListTable 
            users={users}
            onBlock={handleBlockUser}
            onUnblock={handleUnblockUser}
          />
          
          {/* Pagination */}
          {paginationInfo.totalItems > 0 && (
            <div className="mt-4">
              <PaginationComponent 
                paginationInfo={paginationInfo}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </>
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

export default UsersManagementTab; 