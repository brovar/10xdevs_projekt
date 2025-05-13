import React, { useState, useCallback } from 'react';
import useAdminData from '../../../hooks/useAdminData.ts';
import { adminUsersApi } from '../../../services/adminService.ts';
import { UserFiltersState, PaginationData, ConfirmActionState } from '../../../types/viewModels.ts';
import { UserDTO, UserListResponse, UserListQueryParams, UserRole, UserStatus } from '../../../types/api.ts';

import UserFiltersComponent from './UserFiltersComponent.tsx';
import UserListTable from './UserListTable.tsx';
import PaginationComponent from '../../shared/PaginationComponent.tsx';
import ConfirmationModal from '../../shared/ConfirmationModal.tsx';
import LoadingSpinner from '../../shared/LoadingSpinner.tsx';
import ErrorMessageDisplay from '../../shared/ErrorMessageDisplay.tsx';

const UsersManagementTab: React.FC = () => {
  // Modal state for confirmation actions
  const [confirmAction, setConfirmAction] = useState<ConfirmActionState | null>(null);
  
  // Default filters
  const initialFilters: UserFiltersState = {
    page: 1,
    limit: 10
  };

  // Extract items and pagination data from API response
  const extractItems = useCallback((response: UserListResponse): UserDTO[] => {
    return response.items;
  }, []);

  const extractPaginationData = useCallback((response: UserListResponse): PaginationData => {
    return {
      currentPage: response.page,
      totalPages: response.pages,
      totalItems: response.total,
      limit: response.limit
    };
  }, []);

  // Convert UI filter state to API query params
  const convertFiltersToQueryParams = useCallback(
    (filters: UserFiltersState): UserListQueryParams => {
      const queryParams: UserListQueryParams = {
        page: filters.page,
        limit: filters.limit
      };

      if (filters.search) {
        queryParams.search = filters.search;
      }

      if (filters.role) {
        // Type assertion since we know it's a valid UserRole from the UI
        queryParams.role = filters.role as UserRole;
      }

      if (filters.status) {
        // Type assertion since we know it's a valid UserStatus from the UI
        queryParams.status = filters.status as UserStatus;
      }

      return queryParams;
    },
    []
  );

  // Use admin data hook for fetching users with the conversion function
  const { 
    items: users, 
    isLoading, 
    error, 
    paginationData, 
    queryParams,
    handlePageChange,
    handleFiltersChange,
    fetchData
  } = useAdminData<UserFiltersState, UserListResponse, UserDTO>({
    fetchFunction: (filters) => adminUsersApi.getUsers(convertFiltersToQueryParams(filters)),
    initialParams: initialFilters,
    extractItems,
    extractPaginationData
  });

  // Handler for blocking a user
  const handleBlockUser = useCallback((userId: string) => {
    // Find user info for the confirmation message
    const userToBlock = users.find(user => user.id === userId);
    if (!userToBlock) return;

    setConfirmAction({
      type: 'block_user',
      id: userId,
      additionalInfo: `Czy na pewno chcesz zablokować użytkownika ${userToBlock.email}?`
    });
  }, [users]);

  // Handler for unblocking a user
  const handleUnblockUser = useCallback((userId: string) => {
    // Find user info for the confirmation message
    const userToUnblock = users.find(user => user.id === userId);
    if (!userToUnblock) return;

    setConfirmAction({
      type: 'unblock_user',
      id: userId,
      additionalInfo: `Czy na pewno chcesz odblokować użytkownika ${userToUnblock.email}?`
    });
  }, [users]);

  // Handle confirmation for block/unblock actions
  const handleConfirmAction = useCallback(async () => {
    if (!confirmAction) return;

    try {
      if (confirmAction.type === 'block_user') {
        await adminUsersApi.blockUser(confirmAction.id);
      } else if (confirmAction.type === 'unblock_user') {
        await adminUsersApi.unblockUser(confirmAction.id);
      }
      // Refresh the data after action is completed
      fetchData();
    } catch (err) {
      console.error('Action failed:', err);
      // Error handling could be improved with a toast notification
    } finally {
      // Close the confirmation modal
      setConfirmAction(null);
    }
  }, [confirmAction, fetchData]);

  // Close confirmation modal
  const handleCancelAction = () => {
    setConfirmAction(null);
  };

  return (
    <div className="users-management-tab">
      <h2 className="mb-4">Zarządzanie Użytkownikami</h2>
      
      {/* Filters */}
      <UserFiltersComponent 
        currentFilters={queryParams}
        onFilterChange={handleFiltersChange}
      />
      
      {/* Loading state */}
      {isLoading && <LoadingSpinner text="Ładowanie użytkowników..." />}
      
      {/* Error state */}
      {error && !isLoading && (
        <ErrorMessageDisplay error={error} className="mb-4" />
      )}
      
      {/* Users table */}
      {!isLoading && !error && (
        <>
          <UserListTable 
            users={users} 
            onBlock={handleBlockUser}
            onUnblock={handleUnblockUser}
          />
          
          {/* Pagination */}
          {paginationData && (
            <div className="mt-4">
              <PaginationComponent 
                paginationInfo={paginationData}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </>
      )}
      
      {/* Confirmation Modal */}
      {confirmAction && (
        <ConfirmationModal
          isOpen={true}
          title={confirmAction.type === 'block_user' ? 'Blokowanie użytkownika' : 'Odblokowywanie użytkownika'}
          message={confirmAction.additionalInfo || ''}
          onConfirm={handleConfirmAction}
          onCancel={handleCancelAction}
          confirmButtonText={confirmAction.type === 'block_user' ? 'Zablokuj' : 'Odblokuj'}
          variant={confirmAction.type === 'block_user' ? 'warning' : 'primary'}
        />
      )}
    </div>
  );
};

export default UsersManagementTab; 