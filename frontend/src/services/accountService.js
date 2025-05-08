import axios from './api';

/**
 * Fetch user account details
 * @returns {Promise<Object>} User data object
 */
export const fetchAccountDetails = async () => {
  try {
    console.log('Fetching account details...');
    const response = await axios.get('/account');
    console.log('Account details response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error fetching account details:', error.response?.data || error);
    throw error;
  }
};

/**
 * Update user profile information
 * @param {Object} data - Profile data to update (firstName, lastName)
 * @returns {Promise<Object>} Updated user data
 */
export const updateAccountDetails = async (data) => {
  try {
    console.log('Updating account details with:', data);
    const response = await axios.patch('/account', {
      first_name: data.firstName,
      last_name: data.lastName
    });
    console.log('Update account response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error updating account details:', error.response?.data || error);
    throw error;
  }
};

/**
 * Change user password
 * @param {Object} data - Password data (currentPassword, newPassword)
 * @returns {Promise<Object>} Success message
 */
export const changePassword = async (data) => {
  try {
    console.log('Changing password...');
    const response = await axios.put('/account/password', {
      current_password: data.currentPassword,
      new_password: data.newPassword
    });
    console.log('Change password response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error changing password:', error.response?.data || error);
    throw error;
  }
}; 