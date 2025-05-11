import React, { useId, useRef } from 'react';
import PropTypes from 'prop-types';

/**
 * Reusable component for file upload with image preview
 * 
 * @param {Object} props - Component props
 * @param {string} props.label - Input label text
 * @param {string} props.name - Input field name
 * @param {function} props.onChange - Handler for file changes (file) => void
 * @param {function} [props.onRemove] - Handler for removing the current file
 * @param {string} [props.error] - Error message to display
 * @param {string} [props.accept] - Accepted file types (e.g., "image/png,image/jpeg")
 * @param {number} [props.maxSize] - Maximum file size in bytes
 * @param {string} [props.preview] - URL or data URI for image preview
 * @returns {JSX.Element} - Rendered component
 */
const FileUploadInput = ({
  label,
  name,
  onChange,
  onRemove,
  error,
  accept = 'image/png,image/jpeg,image/webp',
  maxSize = 5 * 1024 * 1024, // 5MB default
  preview = null
}) => {
  const id = useId();
  const inputId = `${id}-${name}`;
  const errorId = `${inputId}-error`;
  const fileInputRef = useRef(null);
  
  const handleChange = (e) => {
    const file = e.target.files[0];
    if (!file) {
      onChange(null);
      return;
    }
    
    // Validate file size
    if (file.size > maxSize) {
      // Reset the input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      onChange(null);
      // You might want to show an error message here
      return;
    }
    
    onChange(file);
  };
  
  const handleRemove = () => {
    // Reset the input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    onRemove ? onRemove() : onChange(null);
  };
  
  const handleButtonClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  
  return (
    <div className="mb-3">
      <label htmlFor={inputId} className="form-label">
        {label}
      </label>
      
      <div className={`file-upload ${error ? 'is-invalid' : ''}`}>
        {/* Hidden file input */}
        <input
          type="file"
          className="d-none"
          id={inputId}
          name={name}
          onChange={handleChange}
          accept={accept}
          ref={fileInputRef}
          aria-describedby={error ? errorId : undefined}
          aria-invalid={error ? 'true' : 'false'}
        />
        
        {/* Custom upload UI */}
        <div className="d-flex flex-column">
          <div className="input-group mb-2">
            <button 
              type="button"
              className="btn btn-outline-primary"
              onClick={handleButtonClick}
            >
              Wybierz plik
            </button>
            <span className="form-control text-truncate">
              {preview ? 'Plik wybrany' : 'Nie wybrano pliku'}
            </span>
            {preview && (
              <button 
                type="button"
                className="btn btn-outline-danger"
                onClick={handleRemove}
                aria-label="Usuń plik"
              >
                Usuń
              </button>
            )}
          </div>
          
          {/* Image preview */}
          {preview && (
            <div className="mt-2 border rounded p-2 text-center">
              <img 
                src={preview} 
                alt="Podgląd" 
                className="img-fluid"
                style={{ maxHeight: '200px' }} 
              />
            </div>
          )}
        </div>
        
        {/* Error message */}
        {error && (
          <div 
            id={errorId} 
            className="invalid-feedback d-block"
            aria-live="polite"
          >
            {error}
          </div>
        )}
      </div>
      
      <small className="text-muted d-block mt-1">
        Dozwolone formaty: PNG, JPEG, WebP. Maksymalny rozmiar: {Math.round(maxSize / 1024 / 1024)} MB.
      </small>
    </div>
  );
};

FileUploadInput.propTypes = {
  label: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  onRemove: PropTypes.func,
  error: PropTypes.string,
  accept: PropTypes.string,
  maxSize: PropTypes.number,
  preview: PropTypes.string
};

export default React.memo(FileUploadInput); 