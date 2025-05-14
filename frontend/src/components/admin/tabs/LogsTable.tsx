import React, { useMemo } from 'react';
import { LogDTO } from '../../../types/api';

interface LogsTableProps {
  logs: LogDTO[];
}

const LogsTable: React.FC<LogsTableProps> = ({ logs }) => {
  // Format date - memoized to avoid unnecessary recalculations
  const formatDate = useMemo(() => {
    return (dateString: string) => {
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
  }, []);

  // Format event type for display - replace underscores with spaces and capitalize
  const formatEventType = useMemo(() => {
    return (eventType: string) => {
      return eventType.replace(/_/g, ' ');
    };
  }, []);

  if (logs.length === 0) {
    return (
      <div className="alert alert-info" role="alert">
        No logs matching search criteria.
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <table className="table table-striped table-hover">
        <caption>System logs list</caption>
        <thead className="table-light">
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Event Type</th>
            <th scope="col">User ID</th>
            <th scope="col">IP Address</th>
            <th scope="col">Message</th>
            <th scope="col">Date and Time</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id}>
              <td>{log.id}</td>
              <td>
                <span className="badge bg-secondary">{formatEventType(log.event_type)}</span>
              </td>
              <td>
                {log.user_id ? (
                  <small className="text-muted">{log.user_id.slice(0, 8)}...</small>
                ) : (
                  <span className="text-muted">-</span>
                )}
              </td>
              <td>{log.ip_address || <span className="text-muted">-</span>}</td>
              <td>
                <div className="text-wrap" style={{ maxWidth: '400px', whiteSpace: 'normal' }}>
                  {log.message}
                </div>
              </td>
              <td>{formatDate(log.timestamp)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default LogsTable; 