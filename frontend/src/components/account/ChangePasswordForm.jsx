import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { useForm } from 'react-hook-form';
import { Form, Button, Card, Alert } from 'react-bootstrap';

/**
 * Form for changing user password
 */
const ChangePasswordForm = ({ onSubmit, isSubmitting, error, successMessage }) => {
  const { 
    register, 
    handleSubmit, 
    reset,
    watch,
    formState: { errors } 
  } = useForm({
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmNewPassword: ''
    }
  });

  // Reset form on successful password change
  useEffect(() => {
    if (successMessage) {
      reset();
    }
  }, [successMessage, reset]);

  // Watch newPassword to validate confirmNewPassword
  const newPassword = watch('newPassword');

  // Password validation regex from schemas.py
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9!@#$%^&*(),.?":{}|<>]).{10,}$/;

  return (
    <Card className="mb-4">
      <Card.Header as="h5">Zmień hasło</Card.Header>
      <Card.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        {successMessage && <Alert variant="success">{successMessage}</Alert>}
        
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-3" controlId="password-current">
            <Form.Label>Aktualne hasło</Form.Label>
            <Form.Control
              type="password"
              placeholder="Podaj aktualne hasło"
              {...register("currentPassword", { 
                required: "Aktualne hasło jest wymagane" 
              })}
              isInvalid={!!errors.currentPassword}
            />
            {errors.currentPassword && (
              <Form.Control.Feedback type="invalid">
                {errors.currentPassword.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-3" controlId="password-new">
            <Form.Label>Nowe hasło</Form.Label>
            <Form.Control
              type="password"
              placeholder="Podaj nowe hasło"
              aria-describedby="passwordHelpBlock"
              {...register("newPassword", { 
                required: "Nowe hasło jest wymagane",
                minLength: {
                  value: 10,
                  message: "Hasło musi mieć co najmniej 10 znaków"
                },
                pattern: {
                  value: passwordRegex,
                  message: "Hasło musi zawierać dużą literę, małą literę oraz cyfrę lub znak specjalny"
                }
              })}
              isInvalid={!!errors.newPassword}
            />
            <Form.Text id="passwordHelpBlock" muted>
              Hasło musi mieć minimum 10 znaków, zawierać dużą i małą literę oraz cyfrę lub znak specjalny.
            </Form.Text>
            {errors.newPassword && (
              <Form.Control.Feedback type="invalid">
                {errors.newPassword.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-4" controlId="password-confirm">
            <Form.Label>Potwierdź nowe hasło</Form.Label>
            <Form.Control
              type="password"
              placeholder="Potwierdź nowe hasło"
              {...register("confirmNewPassword", { 
                required: "Potwierdzenie hasła jest wymagane",
                validate: value => value === newPassword || "Hasła nie są zgodne"
              })}
              isInvalid={!!errors.confirmNewPassword}
            />
            {errors.confirmNewPassword && (
              <Form.Control.Feedback type="invalid">
                {errors.confirmNewPassword.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <div className="d-grid gap-2 d-md-flex justify-content-md-end">
            <Button 
              variant="primary" 
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  Przetwarzanie...
                </>
              ) : 'Zmień hasło'}
            </Button>
          </div>
        </Form>
      </Card.Body>
    </Card>
  );
};

ChangePasswordForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  isSubmitting: PropTypes.bool,
  error: PropTypes.string,
  successMessage: PropTypes.string
};

ChangePasswordForm.defaultProps = {
  isSubmitting: false,
  error: null,
  successMessage: null
};

export default ChangePasswordForm; 