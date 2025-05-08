import axios from './api';

export const registerUser = async (userData) => {
  try {
    console.log('Registering user:', userData.email);
    const response = await axios.post('/auth/register', userData);
    console.log('Registration response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Registration error:', error.response?.data || error);
    throw error;
  }
};

export const loginUser = async (credentials) => {
  try {
    console.log('Logging in user:', credentials.email);
    const response = await axios.post('/auth/login', credentials);
    console.log('Login response:', response.data);
    
    // Additional detailed logging
    console.log('Login API response structure:', {
      fullData: JSON.stringify(response.data),
      hasUser: !!response.data?.user,
      user: response.data?.user ? JSON.stringify(response.data.user) : null,
      hasRole: !!response.data?.role || (response.data?.user && !!response.data.user.role),
      role: response.data?.role || (response.data?.user && response.data.user.role)
    });
    
    return response.data;
  } catch (error) {
    console.error('Login error:', error.response?.data || error);
    throw error;
  }
};

export const logoutUser = async () => {
  try {
    console.log('Logging out user');
    const response = await axios.post('/auth/logout');
    console.log('Logout response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Logout error:', error.response?.data || error);
    throw error;
  }
}; 