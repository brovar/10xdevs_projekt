import { useState, useCallback, useEffect } from 'react';
import { PaginationData } from '../types/viewModels';

interface UseAdminDataProps<TQueryParams, TResponse, TItem> {
  fetchFunction: (params: TQueryParams) => Promise<TResponse>;
  initialParams: TQueryParams;
  extractItems: (response: TResponse) => TItem[];
  extractPaginationData: (response: TResponse) => PaginationData;
  dependencies?: any[];
}

function useAdminData<TQueryParams, TResponse, TItem>({
  fetchFunction,
  initialParams,
  extractItems,
  extractPaginationData,
  dependencies = []
}: UseAdminDataProps<TQueryParams, TResponse, TItem>) {
  const [items, setItems] = useState<TItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [queryParams, setQueryParams] = useState<TQueryParams>(initialParams);
  const [paginationData, setPaginationData] = useState<PaginationData | null>(null);

  const fetchData = useCallback(async (params?: Partial<TQueryParams>) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const updatedParams = { ...queryParams, ...params };
      setQueryParams(updatedParams as TQueryParams);
      
      const response = await fetchFunction(updatedParams as TQueryParams);
      const extractedItems = extractItems(response);
      const extractedPaginationData = extractPaginationData(response);
      
      setItems(extractedItems);
      setPaginationData(extractedPaginationData);
    } catch (err) {
      const errorMessage = err instanceof Error 
        ? err.message 
        : 'Wystąpił błąd podczas pobierania danych';
      setError(errorMessage);
      console.error('Error fetching admin data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchFunction, queryParams, extractItems, extractPaginationData]);

  // Handle page change
  const handlePageChange = useCallback((page: number) => {
    fetchData({ page } as Partial<TQueryParams>);
  }, [fetchData]);

  // Handle filters change
  const handleFiltersChange = useCallback((filters: Partial<TQueryParams>) => {
    // Reset to page 1 when filters change
    fetchData({ ...filters, page: 1 } as Partial<TQueryParams>);
  }, [fetchData]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [...dependencies]);

  return {
    items,
    isLoading,
    error,
    paginationData,
    queryParams,
    fetchData,
    handlePageChange,
    handleFiltersChange
  };
}

export default useAdminData; 