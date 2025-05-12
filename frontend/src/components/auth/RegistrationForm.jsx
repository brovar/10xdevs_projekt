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
        watch={watch}
        showPolicy={true}
        rules={{
          required: 'Hasło jest wymagane',
          minLength: {
            value: 10,
            message: 'Hasło musi mieć co najmniej 10 znaków'
          },
          validate: {
            hasUppercase: (value) => 
              /[A-Z]/.test(value) || 'Hasło musi zawierać wielką literę',
            hasLowercase: (value) => 
              /[a-z]/.test(value) || 'Hasło musi zawierać małą literę',
            hasDigitOrSpecial: (value) => 
              /[0-9!@#$%^&*(),.?":{}|<>]/.test(value) || 
              'Hasło musi zawierać cyfrę lub znak specjalny'
          }
        }}
      />

      <PasswordInput
        name="confirmPassword"
        label="Potwierdź hasło"
        register={register}
        errors={errors}
        rules={{
          required: 'Potwierdzenie hasła jest wymagane',
          validate: {
            matchesPassword: (value) => 
              value === getValues('password') || 'Hasła muszą być identyczne'
          }
        }}
      />

      <RoleSelect
        name="role"
        label="Typ konta"
        register={register}
        errors={errors}
        options={[
          { value: UserRole.BUYER, label: 'Kupujący' },
          { value: UserRole.SELLER, label: 'Sprzedający' }
        ]}
        rules={{
          required: 'Wybór typu konta jest wymagany'
        }}
      />

      <SubmitButton
        label="Zarejestruj się"
        isLoading={isLoading}
        disabled={isLoading || !isValid}
      />

      <div className="mt-3 text-center">
        <p>
          Masz już konto? <Link to="/login">Zaloguj się</Link>
        </p>
      </div>
    </form>
  );
};

export default React.memo(RegistrationForm); 