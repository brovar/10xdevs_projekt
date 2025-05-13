import React from 'react';

interface UserInfoItemProps {
  label: string;
  value: React.ReactNode;
  className?: string;
}

const UserInfoItem: React.FC<UserInfoItemProps> = ({ label, value, className = '' }) => {
  return (
    <div className={`user-info-item mb-3 ${className}`}>
      <div className="fw-bold text-secondary small mb-1">{label}</div>
      <div className="user-info-value">
        {value === null || value === undefined || value === '' ? (
          <span className="text-muted">Nie podano</span>
        ) : (
          value
        )}
      </div>
    </div>
  );
};

export default UserInfoItem; 