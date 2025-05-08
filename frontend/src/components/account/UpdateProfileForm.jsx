import React from 'react';
import PropTypes from 'prop-types';
import { useForm } from 'react-hook-form';
import { Form, Button, Card, Alert } from 'react-bootstrap';

/**
 * Form for updating user profile information (first name, last name)
 */
const UpdateProfileForm = ({ initialData, onSubmit, isSubmitting, error }) => {
  const { 
    register, 
    handleSubmit, 
    formState: { errors, isDirty }
  } = useForm({
    defaultValues: {
      firstName: initialData?.firstName || '',
      lastName: initialData?.lastName || ''
    }
  });
  
  const onFormSubmit = (data) => {
    if (isDirty) {
      onSubmit(data);
    }
  };

  return (
    <Card className="mb-4">
      <Card.Header as="h5">Edytuj dane profilu</Card.Header>
      <Card.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        
        <Form onSubmit={handleSubmit(onFormSubmit)}>
          <Form.Group className="mb-3" controlId="profile-firstName">
            <Form.Label>Imię</Form.Label>
            <Form.Control
              type="text"
              placeholder="Podaj imię"
              aria-describedby="firstNameHelpBlock"
              {...register("firstName", { 
                maxLength: { 
                  value: 100, 
                  message: "Imię nie może przekraczać 100 znaków" 
                } 
              })}
              isInvalid={!!errors.firstName}
            />
            <Form.Text id="firstNameHelpBlock" muted>
              Opcjonalne, maksymalnie 100 znaków.
            </Form.Text>
            {errors.firstName && (
              <Form.Control.Feedback type="invalid">
                {errors.firstName.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3" controlId="profile-lastName">
            <Form.Label>Nazwisko</Form.Label>
            <Form.Control
              type="text"
              placeholder="Podaj nazwisko"
              aria-describedby="lastNameHelpBlock"
              {...register("lastName", { 
                maxLength: { 
                  value: 100, 
                  message: "Nazwisko nie może przekraczać 100 znaków" 
                } 
              })}
              isInvalid={!!errors.lastName}
            />
            <Form.Text id="lastNameHelpBlock" muted>
              Opcjonalne, maksymalnie 100 znaków.
            </Form.Text>
            {errors.lastName && (
              <Form.Control.Feedback type="invalid">
                {errors.lastName.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <div className="d-grid gap-2 d-md-flex justify-content-md-end">
            <Button 
              variant="primary" 
              type="submit"
              disabled={isSubmitting || !isDirty}
            >
              {isSubmitting ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Zapisywanie...
                </>
              ) : 'Zapisz zmiany'}
            </Button>
          </div>
        </Form>
      </Card.Body>
    </Card>
  );
};

UpdateProfileForm.propTypes = {
  initialData: PropTypes.shape({
    firstName: PropTypes.string,
    lastName: PropTypes.string
  }),
  onSubmit: PropTypes.func.isRequired,
  isSubmitting: PropTypes.bool,
  error: PropTypes.string
};

UpdateProfileForm.defaultProps = {
  initialData: { firstName: '', lastName: '' },
  isSubmitting: false,
  error: null
};

export default UpdateProfileForm; 