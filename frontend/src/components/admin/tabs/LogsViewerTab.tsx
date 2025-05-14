import React, { useState, useCallback } from 'react';
import useAdminData from '../../../hooks/useAdminData.ts';
import { adminLogsApi } from '../../../services/adminService.ts';
import { LogFiltersState, PaginationData } from '../../../types/viewModels.ts';
import { LogDTO, LogListResponse, AdminLogListQueryParams, LogEventType } from '../../../types/api.ts';

import LogFiltersComponent from './LogFiltersComponent.tsx';
import LogsTable from './LogsTable.tsx';
import PaginationComponent from '../../shared/PaginationComponent.tsx';
import LoadingSpinner from '../../shared/LoadingSpinner.tsx';
import ErrorMessageDisplay from '../../shared/ErrorMessageDisplay.tsx';

const LogsViewerTab: React.FC = () => {
  // Default filters
  const initialFilters: LogFiltersState = {
    page: 1,
    limit: 20
  };

  // Convert UI filter state to API query params
  const convertFiltersToQueryParams = useCallback(
    (filters: LogFiltersState): AdminLogListQueryParams => {
      const queryParams: AdminLogListQueryParams = {
        page: filters.page,
        limit: filters.limit
      };

      if (filters.event_type) {
        // Type assertion since we know it's a valid LogEventType from the UI
        queryParams.event_type = filters.event_type as LogEventType;
      }

      if (filters.user_id) {
        queryParams.user_id = filters.user_id;
      }

      if (filters.ip_address) {
        queryParams.ip_address = filters.ip_address;
      }

      if (filters.start_date) {
        queryParams.start_date = filters.start_date;
      }

      if (filters.end_date) {
        queryParams.end_date = filters.end_date;
      }

      return queryParams;
    },
    []
  );

  // Extract items and pagination data from API response
  const extractItems = useCallback((response: LogListResponse): LogDTO[] => {
    return response.items;
  }, []);

  const extractPaginationData = useCallback((response: LogListResponse): PaginationData => {
    return {
      currentPage: response.page,
      totalPages: response.pages,
      totalItems: response.total,
      limit: response.limit
    };
  }, []);

  // Use admin data hook for fetching logs with the conversion function
  const { 
    items: logs, 
    isLoading, 
    error, 
    paginationData, 
    queryParams,
    handlePageChange,
    handleFiltersChange,
    fetchData
  } = useAdminData<LogFiltersState, LogListResponse, LogDTO>({
    fetchFunction: (filters) => adminLogsApi.getLogs(convertFiltersToQueryParams(filters)),
    initialParams: initialFilters,
    extractItems,
    extractPaginationData
  });

  // Handle fetch retry
  const handleRetry = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="logs-viewer-tab">
      <h2 className="mb-4">System Logs</h2>
      
      {/* Filters */}
      <LogFiltersComponent 
        currentFilters={queryParams}
        onFilterChange={handleFiltersChange}
      />
      
      {/* Loading state */}
      {isLoading && <LoadingSpinner text="Loading logs..." />}
      
      {/* Error state */}
      {error && !isLoading && (
        <ErrorMessageDisplay 
          error={error} 
          className="mb-4" 
          onRetry={handleRetry}
          showDetails={true}
        />
      )}
      
      {/* Logs table */}
      {!isLoading && !error && (
        <>
          <LogsTable logs={logs} />
          
          {/* No logs message */}
          {logs.length === 0 && (
            <div className="alert alert-info" role="status">
              No logs matching search criteria.
            </div>
          )}
          
          {/* Pagination */}
          {paginationData && paginationData.totalItems > 0 && (
            <div className="mt-4">
              <PaginationComponent 
                paginationInfo={paginationData}
                onPageChange={handlePageChange}
                ariaLabel="System logs pagination navigation"
              />
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default LogsViewerTab; 