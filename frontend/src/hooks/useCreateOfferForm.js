import { useState } from 'react';
import { createOffer } from '../services/offerService';

/**
 * Custom hook for managing create offer form state
 * @returns {Object} Form state and handlers
 */
const useCreateOfferForm = () => {
  // Form data state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    quantity: '1', // Default value
    categoryId: '',
    image: null,
    imagePreview: null
  });
  
  // Validation errors state
  const [errors, setErrors] = useState({});
  
  // Form submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [apiError, setApiError] = useState(null);
  
  // Handle text and number input changes
  const handleInputChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error for the changed field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };
  
  // Handle file input changes
  const handleFileChange = (file) => {
    if (file) {
      // Generate preview URL
      const previewUrl = URL.createObjectURL(file);
      setFormData(prev => ({ 
        ...prev, 
        image: file, 
        imagePreview: previewUrl 
      }));
    } else {
      // Clear file and preview
      if (formData.imagePreview) {
        URL.revokeObjectURL(formData.imagePreview);
      }
      
      setFormData(prev => ({ 
        ...prev, 
        image: null, 
        imagePreview: null 
      }));
    }
    
    // Clear error for the image field
    if (errors.image) {
      setErrors(prev => ({ ...prev, image: undefined }));
    }
  };
  
  // Validate the form
  const validateForm = () => {
    const newErrors = {};
    
    // Validate title (required)
    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }
    
    // Validate price (required, must be a positive number)
    if (!formData.price.trim()) {
      newErrors.price = 'Price is required';
    } else {
      const priceValue = parseFloat(formData.price.replace(',', '.'));
      if (isNaN(priceValue) || priceValue <= 0) {
        newErrors.price = 'Price must be a number greater than 0';
      }
    }
    
    // Validate quantity (must be a non-negative integer)
    if (formData.quantity.trim()) {
      const quantityValue = parseInt(formData.quantity, 10);
      if (isNaN(quantityValue) || quantityValue < 0) {
        newErrors.quantity = 'Quantity must be a non-negative number';
      }
    }
    
    // Validate category (required)
    if (!formData.categoryId) {
      newErrors.categoryId = 'Category is required';
    }
    
    // Update errors state
    setErrors(newErrors);
    
    // Return true if there are no errors
    return Object.keys(newErrors).length === 0;
  };
  
  // Submit the form
  const submitForm = async () => {
    // Validate form before submitting
    if (!validateForm()) {
      return null;
    }
    
    setIsSubmitting(true);
    setApiError(null);
    
    try {
      // Create FormData object for file upload
      const formDataToSend = new FormData();
      formDataToSend.append('title', formData.title);
      
      if (formData.description) {
        formDataToSend.append('description', formData.description);
      }
      
      formDataToSend.append('price', formData.price.replace(',', '.'));
      formDataToSend.append('quantity', formData.quantity || '1');
      formDataToSend.append('category_id', formData.categoryId);
      
      if (formData.image) {
        formDataToSend.append('image', formData.image);
      }
      
      // Send API request using the service
      const newOffer = await createOffer(formDataToSend);
      setIsSuccess(true);
      
      // Return the new offer data
      return newOffer;
    } catch (error) {
      // Handle error
      setApiError(error.message || 'An unknown error occurred');
      return null;
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Return the form state and handlers
  return {
    formData,
    errors,
    isSubmitting,
    isSuccess,
    apiError,
    handleInputChange,
    handleFileChange,
    validateForm,
    submitForm,
  };
};

export default useCreateOfferForm; 