import axios from 'axios';

// Set default config for axios
axios.defaults.baseURL = 'http://localhost:8000';
axios.defaults.withCredentials = true; // Important for cookies/session

// Add a request interceptor to include credentials and proper headers
axios.interceptors.request.use(
  config => {
    // Add authorization header if needed
    const user = localStorage.getItem('user');
    if (user) {
      try {
        const userData = JSON.parse(user);
        if (userData.token) {
          config.headers.Authorization = `Bearer ${userData.token}`;
        }
      } catch (error) {
        console.error('Error parsing user data from localStorage:', error);
      }
    }
    return config;
  },
  error => Promise.reject(error)
);

// Add a response interceptor for debugging
axios.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    console.error('API Error:', error.response || error);
    return Promise.reject(error);
  }
);

export default axios; 