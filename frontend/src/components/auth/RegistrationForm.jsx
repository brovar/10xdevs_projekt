import React from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import EmailInput from '../common/forms/EmailInput';
import PasswordInput from '../common/forms/PasswordInput';
import RoleSelect from '../common/forms/RoleSelect';
import SubmitButton from '../common/forms/SubmitButton';

// Enum values matching the backend
const UserRole = {
  BUYER: "Buyer",
  SELLER: "Seller"
};

const RegistrationForm = ({ onSubmit, isLoading }) => {
  const { 
    register, 
    handleSubmit, 
    watch, 
    getValues,
    formState: { errors, isValid } 
  } = useForm({
    mode: 'onBlur',
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      role: ''
    }
  });

  const processSubmit = (data) => {
    // Remove confirmPassword before sending to API
    const { confirmPassword, ...registerData } = data;
    
    // Log the data for debugging
    console.log('Registration form submission:', { 
      email: registerData.email,
      role: registerData.role 
    });
    
    onSubmit(registerData);
  };

  return (
    <form onSubmit={handleSubmit(processSubmit)}>
      <EmailInput
        name="email"
        label="Email address"
        register={register}
        errors={errors}
        rules={{
          required: 'Email address is required',
          pattern: {
            value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
            message: 'Invalid email format'
          }
        }}
      />

      <PasswordInput
        name="password"
        label="Password"
        register={register}
        errors={errors}
        watch={watch}
        showPolicy={true}
        rules={{
          required: 'Password is required',
          minLength: {
            value: 10,
            message: 'Password must be at least 10 characters'
          },
          validate: {
            hasUppercase: (value) => 
              /[A-Z]/.test(value) || 'Password must contain an uppercase letter',
            hasLowercase: (value) => 
              /[a-z]/.test(value) || 'Password must contain a lowercase letter',
            hasDigitOrSpecial: (value) => 
              /[0-9!@#$%^&*(),.?":{}|<>]/.test(value) || 
              'Password must contain a digit or special character'
          }
        }}
      />

      <PasswordInput
        name="confirmPassword"
        label="Confirm password"
        register={register}
        errors={errors}
        rules={{
          required: 'Password confirmation is required',
          validate: {
            matchesPassword: (value) => 
              value === getValues('password') || 'Passwords must match'
          }
        }}
      />

      <RoleSelect
        name="role"
        label="Account type"
        register={register}
        errors={errors}
        options={[
          { value: UserRole.BUYER, label: 'Buyer' },
          { value: UserRole.SELLER, label: 'Seller' }
        ]}
        rules={{
          required: 'Account type selection is required'
        }}
      />

      <SubmitButton
        label="Register"
        isLoading={isLoading}
        disabled={isLoading || !isValid}
      />

      <div className="mt-3 text-center">
        <p>
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </form>
  );
};

export default React.memo(RegistrationForm); 