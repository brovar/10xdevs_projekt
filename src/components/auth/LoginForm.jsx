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
        label="Adres email"
        register={register}
        errors={errors}
        rules={{
          required: 'Adres email jest wymagany',
          pattern: {
            value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
            message: 'Niepoprawny format adresu email'
          }
        }}
      />

      <PasswordInput
        name="password"
        label="Hasło"
        register={register}
        errors={errors}
        rules={{
          required: 'Hasło jest wymagane'
        }}
      />

      <SubmitButton
        label="Zaloguj się"
        isLoading={isLoading}
        disabled={isLoading || !isValid}
      />

      <div className="mt-3 text-center">
        <p>
          Nie masz konta? <Link to="/register">Zarejestruj się</Link>
        </p>
      </div>
    </form>
  );
};

export default React.memo(LoginForm); 