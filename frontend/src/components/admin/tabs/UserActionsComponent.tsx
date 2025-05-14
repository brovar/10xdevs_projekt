import React from 'react';
import { Link } from 'react-router-dom';
import { UserDTO, UserStatus } from '../../../types/api';

interface UserActionsProps {
  user: UserDTO;
  onBlock: (userId: string) => void;
  onUnblock: (userId: string) => void;
}

const UserActionsComponent: React.FC<UserActionsProps> = ({ user, onBlock, onUnblock }) => {
  const isActive = user.status === UserStatus.ACTIVE;
  const isInactive = user.status === UserStatus.INACTIVE;
  
  return (
    <div className="d-flex gap-2">
      {/* View details button */}
      <Link 
        to={`/admin/users/${user.id}`} 
        className="btn btn-sm btn-outline-primary"
        aria-label={`View details of user ${user.email}`}
      >
        <i className="bi bi-eye"></i> Details
      </Link>
      
      {/* Block button - only shown for active users */}
      {isActive && (
        <button
          type="button"
          className="btn btn-sm btn-warning"
          onClick={() => onBlock(user.id)}
          aria-label={`Block user ${user.email}`}
        >
          <i className="bi bi-slash-circle"></i> Block
        </button>
      )}
      
      {/* Unblock button - only shown for inactive users */}
      {isInactive && (
        <button
          type="button"
          className="btn btn-sm btn-success"
          onClick={() => onUnblock(user.id)}
          aria-label={`Unblock user ${user.email}`}
        >
          <i className="bi bi-check-circle"></i> Unblock
        </button>
      )}
    </div>
  );
};

export default UserActionsComponent; 