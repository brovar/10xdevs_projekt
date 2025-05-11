import { useState, useEffect } from 'react';
import { fetchCategories } from '../services/offerService';

/**
 * Custom hook for fetching the list of categories
 * @returns {Object} Categories data and loading state
 */
const useCategoriesList = () => {
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const getCategoriesList = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const data = await fetchCategories();
        setCategories(data.items || []);
      } catch (error) {
        console.error('Error fetching categories:', error);
        setError(error.message || 'Wystąpił błąd podczas pobierania kategorii');
      } finally {
        setIsLoading(false);
      }
    };
    
    getCategoriesList();
  }, []);
  
  // Transform categories to options format for select input
  const categoryOptions = categories.map(category => ({
    value: category.id.toString(),
    label: category.name
  }));
  
  return { 
    categories,
    categoryOptions, 
    isLoading, 
    error 
  };
};

export default useCategoriesList; 