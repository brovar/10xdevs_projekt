import React, { useMemo } from 'react';
import { UserDTO } from '../../types/api.ts';
import UserInfoItem from './UserInfoItem.tsx';
import StatusBadge from '../shared/StatusBadge.tsx';

interface UserDetailsPanelProps {
  user: UserDTO;
}

const UserDetailsPanel: React.FC<UserDetailsPanelProps> = ({ user }) => {
  // Format date - memoized to avoid unnecessary recalculations
  const formatDate = useMemo(() => {
    return (dateString: string | null | undefined) => {
      if (!dateString) return 'N/A';
      
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

  return (
    <div className="user-details-panel">
      <div className="card">
        <div className="card-header bg-light">
          <h5 className="card-title mb-0">User Information</h5>
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
              <UserInfoItem 
                label="Role" 
                value={user.role} 
              />
              <UserInfoItem 
                label="Status" 
                value={<StatusBadge status={user.status} />} 
              />
              <UserInfoItem 
                label="Created at" 
                value={formatDate(user.created_at)} 
              />
              <UserInfoItem 
                label="Updated at" 
                value={formatDate(user.updated_at)} 
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserDetailsPanel; 