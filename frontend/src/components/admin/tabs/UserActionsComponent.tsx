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
        aria-label={`Zobacz szczegóły użytkownika ${user.email}`}
      >
        <i className="bi bi-eye"></i> Szczegóły
      </Link>
      
      {/* Block button - only shown for active users */}
      {isActive && (
        <button
          type="button"
          className="btn btn-sm btn-warning"
          onClick={() => onBlock(user.id)}
          aria-label={`Zablokuj użytkownika ${user.email}`}
        >
          <i className="bi bi-slash-circle"></i> Zablokuj
        </button>
      )}
      
      {/* Unblock button - only shown for inactive users */}
      {isInactive && (
        <button
          type="button"
          className="btn btn-sm btn-success"
          onClick={() => onUnblock(user.id)}
          aria-label={`Odblokuj użytkownika ${user.email}`}
        >
          <i className="bi bi-check-circle"></i> Odblokuj
        </button>
      )}
    </div>
  );
};

export default UserActionsComponent; 