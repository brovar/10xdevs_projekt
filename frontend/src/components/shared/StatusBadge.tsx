import React from 'react';
import { UserStatus, OfferStatus, OrderStatus } from '../../types/api';

// Define types for status values
type StatusValue = UserStatus | OfferStatus | OrderStatus | string;

// Define color mappings with improved contrast for accessibility
// Using bg-* and text-* classes to ensure proper contrast ratios
interface StatusStyleConfig {
  bgClass: string;
  textClass: string;
  icon?: string;
}

const statusStyleMap: Record<string, StatusStyleConfig> = {
  // User status styles
  'Active': { bgClass: 'bg-success-subtle', textClass: 'text-success-emphasis', icon: 'bi-check-circle' },
  'Inactive': { bgClass: 'bg-warning-subtle', textClass: 'text-warning-emphasis', icon: 'bi-pause-circle' },
  'Deleted': { bgClass: 'bg-danger-subtle', textClass: 'text-danger-emphasis', icon: 'bi-x-circle' },
  
  // Offer status styles
  'active': { bgClass: 'bg-success-subtle', textClass: 'text-success-emphasis', icon: 'bi-check-circle' },
  'inactive': { bgClass: 'bg-secondary-subtle', textClass: 'text-secondary-emphasis', icon: 'bi-pause-circle' },
  'sold': { bgClass: 'bg-info-subtle', textClass: 'text-info-emphasis', icon: 'bi-bag-check' },
  'moderated': { bgClass: 'bg-primary-subtle', textClass: 'text-primary-emphasis', icon: 'bi-shield-check' },
  'archived': { bgClass: 'bg-secondary-subtle', textClass: 'text-secondary-emphasis', icon: 'bi-archive' },
  'deleted': { bgClass: 'bg-danger-subtle', textClass: 'text-danger-emphasis', icon: 'bi-trash' },
  
  // Order status styles
  'pending_payment': { bgClass: 'bg-warning-subtle', textClass: 'text-warning-emphasis', icon: 'bi-clock' },
  'processing': { bgClass: 'bg-info-subtle', textClass: 'text-info-emphasis', icon: 'bi-gear' },
  'shipped': { bgClass: 'bg-primary-subtle', textClass: 'text-primary-emphasis', icon: 'bi-truck' },
  'delivered': { bgClass: 'bg-success-subtle', textClass: 'text-success-emphasis', icon: 'bi-box-seam' },
  'cancelled': { bgClass: 'bg-danger-subtle', textClass: 'text-danger-emphasis', icon: 'bi-x-circle' },
  'failed': { bgClass: 'bg-danger-subtle', textClass: 'text-danger-emphasis', icon: 'bi-exclamation-triangle' },
  
  // Default style
  'default': { bgClass: 'bg-secondary-subtle', textClass: 'text-secondary-emphasis', icon: 'bi-question-circle' }
};

interface StatusBadgeProps {
  status: StatusValue;
  className?: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  // Get the status text for display (capitalize first letter if using underscores)
  const displayText = status.includes('_') 
    ? status.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
    : status;

  // Get appropriate style based on status
  const statusKey = status.toString();
  const style = statusStyleMap[statusKey] || statusStyleMap.default;
  
  return (
    <span 
      className={`d-inline-flex align-items-center px-2 py-1 rounded ${style.bgClass} ${style.textClass} ${className}`}
      role="status"
      aria-label={`Status: ${displayText}`}
    >
      {style.icon && (
        <i className={`${style.icon} me-1`} aria-hidden="true"></i>
      )}
      {displayText}
    </span>
  );
};

export default StatusBadge; 