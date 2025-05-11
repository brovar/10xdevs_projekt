import React, { useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import TextInput from '../common/forms/TextInput';
import TextArea from '../common/forms/TextArea';
import NumberInput from '../common/forms/NumberInput';
import SelectInput from '../common/forms/SelectInput';
import FileUploadInput from '../common/forms/FileUploadInput';
import ValidationError from '../common/forms/ValidationError';
import SubmitButton from '../common/forms/SubmitButton';
import useCreateOfferForm from '../../hooks/useCreateOfferForm';
import useCategoriesList from '../../hooks/useCategoriesList';

/**
 * Form component for creating/editing offers
 * 
 * @param {Object} props - Component props
 * @param {Function} props.onSuccess - Callback after successful form submission
 * @param {Function} props.onCancel - Callback for canceling the form
 * @returns {JSX.Element} - Rendered component
 */
const OfferForm = ({ onSuccess, onCancel }) => {
  // Get form state and handlers from custom hook
  const {
    formData,
    errors,
    isSubmitting,
    apiError,
    handleInputChange,
    handleFileChange,
    submitForm
  } = useCreateOfferForm();
  
  // Get categories from API
  const { categoryOptions, isLoading: categoriesLoading, error: categoriesError } = useCategoriesList();
  
  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const newOffer = await submitForm();
    
    if (newOffer && onSuccess) {
      onSuccess(newOffer);
    }
  };
  
  // Handle input blur for validation
  const handleBlur = useCallback((field) => {
    // Implement field-specific validation on blur if needed
  }, []);
  
  // Handle cancel button click
  const handleCancel = (e) => {
    e.preventDefault();
    if (onCancel) {
      onCancel();
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="needs-validation" noValidate>
      {/* Title field */}
      <TextInput
        label="Tytuł oferty"
        name="title"
        value={formData.title}
        onChange={handleInputChange}
        onBlur={() => handleBlur('title')}
        error={errors.title}
        required
        placeholder="Wpisz tytuł oferty"
      />
      
      {/* Description field */}
      <TextArea
        label="Opis"
        name="description"
        value={formData.description}
        onChange={handleInputChange}
        onBlur={() => handleBlur('description')}
        error={errors.description}
        placeholder="Opisz swój produkt"
        rows={5}
      />
      
      {/* Price field */}
      <NumberInput
        label="Cena (PLN)"
        name="price"
        value={formData.price}
        onChange={handleInputChange}
        onBlur={() => handleBlur('price')}
        error={errors.price}
        required
        min={0}
        step="0.01"
        isDecimal={true}
        placeholder="0.00"
      />
      
      {/* Quantity field */}
      <NumberInput
        label="Ilość"
        name="quantity"
        value={formData.quantity}
        onChange={handleInputChange}
        onBlur={() => handleBlur('quantity')}
        error={errors.quantity}
        min={0}
        step="1"
        isDecimal={false}
        placeholder="1"
      />
      
      {/* Category select */}
      <SelectInput
        label="Kategoria"
        name="categoryId"
        value={formData.categoryId}
        options={categoryOptions}
        onChange={handleInputChange}
        onBlur={() => handleBlur('categoryId')}
        error={errors.categoryId || (categoriesError && 'Nie można załadować kategorii')}
        required
        placeholder={categoriesLoading ? 'Ładowanie kategorii...' : 'Wybierz kategorię'}
      />
      
      {/* Image upload */}
      <FileUploadInput
        label="Zdjęcie produktu"
        name="image"
        onChange={handleFileChange}
        error={errors.image}
        accept="image/png,image/jpeg,image/webp"
        preview={formData.imagePreview}
      />
      
      {/* API error message */}
      {apiError && <ValidationError message={apiError} />}
      
      {/* Form buttons */}
      <div className="d-flex justify-content-between mt-4">
        <button
          type="button"
          className="btn btn-outline-secondary"
          onClick={handleCancel}
          disabled={isSubmitting}
        >
          Anuluj
        </button>
        
        <SubmitButton
          label="Zapisz ofertę"
          isLoading={isSubmitting}
          disabled={categoriesLoading}
        />
      </div>
    </form>
  );
};

OfferForm.propTypes = {
  onSuccess: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired
};

export default React.memo(OfferForm);