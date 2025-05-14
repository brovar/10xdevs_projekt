import React from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import EmailInput from '../common/forms/EmailInput';
import PasswordInput from '../common/forms/PasswordInput';
import SubmitButton from '../common/forms/SubmitButton';

const LoginForm = ({ onSubmit, isLoading }) => {
  const { 
    register, 
    handleSubmit, 
    formState: { errors, isValid } 
  } = useForm({
    mode: 'onBlur',
    defaultValues: {
      email: '',
      password: ''
    }
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
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
        rules={{
          required: 'Password is required'
        }}
      />

      <SubmitButton
        label="Log in"
        isLoading={isLoading}
        disabled={isLoading || !isValid}
      />

      <div className="mt-3 text-center">
        <p>
          Don't have an account? <Link to="/register">Register</Link>
        </p>
      </div>
    </form>
  );
};

export default React.memo(LoginForm); 