import React, { useMemo } from 'react';
import { UserDTO } from '../../../types/api';
import UserActionsComponent from './UserActionsComponent.tsx';
import StatusBadge from '../../shared/StatusBadge.tsx';

interface UserListTableProps {
  users: UserDTO[];
  onBlock: (userId: string) => void;
  onUnblock: (userId: string) => void;
}

const UserListTable: React.FC<UserListTableProps> = ({ users, onBlock, onUnblock }) => {
  // Format date - memoized to avoid unnecessary recalculations
  const formatDate = useMemo(() => {
    return (dateString: string) => {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat('en-US', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    };
  }, []);

  if (users.length === 0) {
    return (
      <div className="alert alert-info">
        No users matching search criteria.
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <table className="table table-striped table-hover">
        <thead className="table-light">
          <tr>
            <th scope="col">Email</th>
            <th scope="col">Full Name</th>
            <th scope="col">Role</th>
            <th scope="col">Status</th>
            <th scope="col">Created at</th>
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

export default UserListTable; 