import { 
  UserDTO, 
  UserListResponse, 
  UserStatus,
  UserRole,
  UserListQueryParams
} from '../types/api';

// Mock user data
const mockUsers: UserDTO[] = [
  {
    id: '1',
    email: 'admin@example.com',
    role: UserRole.ADMIN,
    status: UserStatus.ACTIVE,
    first_name: 'Admin',
    last_name: 'User',
    created_at: new Date(2023, 0, 1).toISOString()
  },
  {
    id: '2',
    email: 'seller@example.com',
    role: UserRole.SELLER,
    status: UserStatus.ACTIVE,
    first_name: 'Seller',
    last_name: 'User',
    created_at: new Date(2023, 0, 15).toISOString()
  },
  {
    id: '3',
    email: 'buyer@example.com',
    role: UserRole.BUYER,
    status: UserStatus.ACTIVE,
    first_name: 'Buyer',
    last_name: 'User',
    created_at: new Date(2023, 1, 1).toISOString()
  },
  {
    id: '4',
    email: 'blocked@example.com',
    role: UserRole.SELLER,
    status: UserStatus.INACTIVE,
    first_name: 'Blocked',
    last_name: 'User',
    created_at: new Date(2022, 11, 1).toISOString()
  },
  {
    id: '5',
    email: 'john.doe@example.com',
    role: UserRole.BUYER,
    status: UserStatus.ACTIVE,
    first_name: 'John',
    last_name: 'Doe',
    created_at: new Date(2023, 2, 15).toISOString()
  },
  {
    id: '6',
    email: 'jane.doe@example.com',
    role: UserRole.BUYER,
    status: UserStatus.ACTIVE,
    first_name: 'Jane',
    last_name: 'Doe',
    created_at: new Date(2023, 3, 10).toISOString()
  },
  {
    id: '7',
    email: 'alice@example.com',
    role: UserRole.SELLER,
    status: UserStatus.ACTIVE,
    first_name: 'Alice',
    last_name: 'Smith',
    created_at: new Date(2023, 2, 5).toISOString()
  },
  {
    id: '8',
    email: 'bob@example.com',
    role: UserRole.SELLER,
    status: UserStatus.ACTIVE,
    first_name: 'Bob',
    last_name: 'Johnson',
    created_at: new Date(2023, 1, 20).toISOString()
  },
  {
    id: '9',
    email: 'charlie@example.com',
    role: UserRole.BUYER,
    status: UserStatus.INACTIVE,
    first_name: 'Charlie',
    last_name: 'Brown',
    created_at: new Date(2022, 10, 15).toISOString()
  },
  {
    id: '10',
    email: 'david@example.com',
    role: UserRole.BUYER,
    status: UserStatus.ACTIVE,
    first_name: 'David',
    last_name: 'Williams',
    created_at: new Date(2023, 4, 5).toISOString()
  },
  {
    id: '11',
    email: 'emma@example.com',
    role: UserRole.SELLER,
    status: UserStatus.ACTIVE,
    first_name: 'Emma',
    last_name: 'Taylor',
    created_at: new Date(2023, 3, 25).toISOString()
  },
  {
    id: '12',
    email: 'frank@example.com',
    role: UserRole.BUYER,
    status: UserStatus.ACTIVE,
    first_name: 'Frank',
    last_name: 'Miller',
    created_at: new Date(2023, 5, 10).toISOString()
  }
];

// Helper function to filter users
const filterUsers = (users: UserDTO[], params: UserListQueryParams): UserDTO[] => {
  return users.filter(user => {
    // Filter by role if specified
    if (params.role && user.role !== params.role) {
      return false;
    }
    
    // Filter by status if specified
    if (params.status && user.status !== params.status) {
      return false;
    }
    
    // Filter by search if specified
    if (params.search) {
      const searchLower = params.search.toLowerCase();
      const email = user.email.toLowerCase();
      const firstName = user.first_name?.toLowerCase() || '';
      const lastName = user.last_name?.toLowerCase() || '';
      
      if (!email.includes(searchLower) && 
          !firstName.includes(searchLower) && 
          !lastName.includes(searchLower)) {
        return false;
      }
    }
    
    return true;
  });
};

// Helper function to delay response (simulating network)
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock Admin Users API
export const mockAdminUsersApi = {
  // Get users list
  getUsers: async (params: UserListQueryParams): Promise<UserListResponse> => {
    // Simulate network delay
    await delay(500);
    
    // Apply filters
    const filteredUsers = filterUsers(mockUsers, params);
    
    // Apply pagination
    const page = params.page || 1;
    const limit = params.limit || 10;
    const start = (page - 1) * limit;
    const end = start + limit;
    const paginatedUsers = filteredUsers.slice(start, end);
    
    return {
      items: paginatedUsers,
      total: filteredUsers.length,
      page,
      limit,
      pages: Math.ceil(filteredUsers.length / limit)
    };
  },

  // Get user details
  getUserDetails: async (userId: string): Promise<UserDTO> => {
    // Simulate network delay
    await delay(500);
    
    const user = mockUsers.find(u => u.id === userId);
    
    if (!user) {
      throw new Error('User not found');
    }
    
    return user;
  },

  // Block user
  blockUser: async (userId: string): Promise<UserDTO> => {
    // Simulate network delay
    await delay(800);
    
    const userIndex = mockUsers.findIndex(u => u.id === userId);
    
    if (userIndex === -1) {
      throw new Error('User not found');
    }
    
    if (mockUsers[userIndex].status === UserStatus.INACTIVE) {
      throw new Error('User is already blocked');
    }
    
    // Update user status in our mock data
    mockUsers[userIndex] = {
      ...mockUsers[userIndex],
      status: UserStatus.INACTIVE,
      updated_at: new Date().toISOString()
    };
    
    return mockUsers[userIndex];
  },

  // Unblock user
  unblockUser: async (userId: string): Promise<UserDTO> => {
    // Simulate network delay
    await delay(800);
    
    const userIndex = mockUsers.findIndex(u => u.id === userId);
    
    if (userIndex === -1) {
      throw new Error('User not found');
    }
    
    if (mockUsers[userIndex].status === UserStatus.ACTIVE) {
      throw new Error('User is already active');
    }
    
    // Update user status in our mock data
    mockUsers[userIndex] = {
      ...mockUsers[userIndex],
      status: UserStatus.ACTIVE,
      updated_at: new Date().toISOString()
    };
    
    return mockUsers[userIndex];
  },
}; 