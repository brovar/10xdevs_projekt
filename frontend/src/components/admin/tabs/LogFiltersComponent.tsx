import React, { useState, useEffect } from 'react';
import { LogEventType } from '../../../types/api';
import { LogFiltersState } from '../../../types/viewModels';

interface LogFiltersComponentProps {
  currentFilters: LogFiltersState;
  onFilterChange: (filters: Partial<LogFiltersState>) => void;
}

const LogFiltersComponent: React.FC<LogFiltersComponentProps> = ({
  currentFilters,
  onFilterChange
}) => {
  const [localFilters, setLocalFilters] = useState<LogFiltersState>(currentFilters);
  const [dateError, setDateError] = useState<string | null>(null);

  // Update local state when props change
  useEffect(() => {
    setLocalFilters(currentFilters);
  }, [currentFilters]);

  // Handle input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    // Clear date error when date fields change
    if (name === 'start_date' || name === 'end_date') {
      setDateError(null);
    }
    
    setLocalFilters(prev => ({
      ...prev,
      [name]: value || undefined // Convert empty string to undefined
    }));
  };

  // Validate date range before submitting
  const validateDateRange = (): boolean => {
    const { start_date, end_date } = localFilters;
    
    // If both dates are provided, ensure end_date is not before start_date
    if (start_date && end_date) {
      const startDateTime = new Date(start_date).getTime();
      const endDateTime = new Date(end_date).getTime();
      
      if (endDateTime < startDateTime) {
        setDateError('End date cannot be earlier than start date');
        return false;
      }
    }
    
    setDateError(null);
    return true;
  };

  // Apply filters
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateDateRange()) {
      onFilterChange(localFilters);
    }
  };

  // Reset filters
  const handleReset = () => {
    const resetFilters = {
      event_type: undefined,
      user_id: undefined,
      ip_address: undefined,
      start_date: undefined,
      end_date: undefined,
      page: 1,
      limit: currentFilters.limit
    };
    setLocalFilters(resetFilters);
    setDateError(null);
    onFilterChange(resetFilters);
  };

  return (
    <div className="card mb-4">
      <div className="card-body">
        <h5 className="card-title">Log Filters</h5>
        <form onSubmit={handleSubmit}>
          <div className="row g-3">
            {/* Event Type filter */}
            <div className="col-12 col-md-4">
              <label htmlFor="event_type" className="form-label">Event Type</label>
              <select
                className="form-select"
                id="event_type"
                name="event_type"
                value={localFilters.event_type || ''}
                onChange={handleInputChange}
                aria-describedby="eventTypeHelp"
              >
                <option value="">All event types</option>
                {Object.values(LogEventType).map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
              <div id="eventTypeHelp" className="form-text">Filter logs by event type</div>
            </div>

            {/* User ID filter */}
            <div className="col-12 col-md-4">
              <label htmlFor="user_id" className="form-label">User ID</label>
              <input
                type="text"
                className="form-control"
                id="user_id"
                name="user_id"
                placeholder="User UUID"
                value={localFilters.user_id || ''}
                onChange={handleInputChange}
                aria-describedby="userIdHelp"
              />
              <div id="userIdHelp" className="form-text">Logs for a specific user</div>
            </div>

            {/* IP Address filter */}
            <div className="col-12 col-md-4">
              <label htmlFor="ip_address" className="form-label">IP Address</label>
              <input
                type="text"
                className="form-control"
                id="ip_address"
                name="ip_address"
                placeholder="e.g. 192.168.1.1"
                value={localFilters.ip_address || ''}
                onChange={handleInputChange}
                aria-describedby="ipAddressHelp"
              />
              <div id="ipAddressHelp" className="form-text">Logs from a specific IP address</div>
            </div>

            {/* Start Date filter */}
            <div className="col-12 col-md-6">
              <label htmlFor="start_date" className="form-label">Start Date</label>
              <input
                type="datetime-local"
                className="form-control"
                id="start_date"
                name="start_date"
                value={localFilters.start_date || ''}
                onChange={handleInputChange}
                aria-describedby="startDateHelp"
              />
              <div id="startDateHelp" className="form-text">Logs from this date and time</div>
            </div>

            {/* End Date filter */}
            <div className="col-12 col-md-6">
              <label htmlFor="end_date" className="form-label">End Date</label>
              <input
                type="datetime-local"
                className="form-control"
                id="end_date"
                name="end_date"
                value={localFilters.end_date || ''}
                onChange={handleInputChange}
                aria-describedby="endDateHelp"
              />
              <div id="endDateHelp" className="form-text">Logs until this date and time</div>
            </div>

            {/* Date range error display */}
            {dateError && (
              <div className="col-12">
                <div className="alert alert-danger" role="alert">
                  {dateError}
                </div>
              </div>
            )}

            {/* Action buttons */}
            <div className="col-12 d-flex justify-content-end mt-3">
              <button
                type="button"
                className="btn btn-outline-secondary me-2"
                onClick={handleReset}
              >
                Reset
              </button>
              <button type="submit" className="btn btn-primary">
                Apply Filters
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LogFiltersComponent; 