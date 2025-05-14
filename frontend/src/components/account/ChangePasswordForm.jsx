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
      <Card.Header as="h5">Change Password</Card.Header>
      <Card.Body>
        {error && <Alert variant="danger">{error}</Alert>}
        {successMessage && <Alert variant="success">{successMessage}</Alert>}
        
        <Form onSubmit={handleSubmit(onSubmit)}>
          <Form.Group className="mb-3" controlId="password-current">
            <Form.Label>Current Password</Form.Label>
            <Form.Control
              type="password"
              placeholder="Enter current password"
              {...register("currentPassword", { 
                required: "Current password is required" 
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
            <Form.Label>New Password</Form.Label>
            <Form.Control
              type="password"
              placeholder="Enter new password"
              aria-describedby="passwordHelpBlock"
              {...register("newPassword", { 
                required: "New password is required",
                minLength: {
                  value: 10,
                  message: "Password must be at least 10 characters long"
                },
                pattern: {
                  value: passwordRegex,
                  message: "Password must contain uppercase letter, lowercase letter, and a digit or special character"
                }
              })}
              isInvalid={!!errors.newPassword}
            />
            <Form.Text id="passwordHelpBlock" muted>
              Password must be at least 10 characters long, contain uppercase and lowercase letters, and a digit or special character.
            </Form.Text>
            {errors.newPassword && (
              <Form.Control.Feedback type="invalid">
                {errors.newPassword.message}
              </Form.Control.Feedback>
            )}
          </Form.Group>

          <Form.Group className="mb-4" controlId="password-confirm">
            <Form.Label>Confirm New Password</Form.Label>
            <Form.Control
              type="password"
              placeholder="Confirm new password"
              {...register("confirmNewPassword", { 
                required: "Password confirmation is required",
                validate: value => value === newPassword || "Passwords do not match"
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
                  Processing...
                </>
              ) : 'Change Password'}
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