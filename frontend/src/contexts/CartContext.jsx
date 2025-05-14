import React, { createContext, useContext, useEffect, useReducer, useCallback } from 'react';
import PropTypes from 'prop-types';

// Actions for reducer
const ADD_TO_CART = 'ADD_TO_CART';
const REMOVE_FROM_CART = 'REMOVE_FROM_CART';
const UPDATE_QUANTITY = 'UPDATE_QUANTITY';
const CLEAR_CART = 'CLEAR_CART';
const INIT_CART = 'INIT_CART';

// Reducer for managing cart state
const cartReducer = (state, action) => {
  switch (action.type) {
    case INIT_CART:
      return action.payload;
    case ADD_TO_CART: {
      const { offerId, quantity = 1, offer } = action.payload;
      const existingItem = state.find(item => item.offerId === offerId);
      
      if (existingItem) {
        return state.map(item => 
          item.offerId === offerId 
            ? { ...item, quantity: Math.min(item.quantity + quantity, 20) } 
            : item
        );
      } else {
        return [...state, { offerId, quantity, offer }];
      }
    }
    case REMOVE_FROM_CART:
      return state.filter(item => item.offerId !== action.payload);
    case UPDATE_QUANTITY: {
      const { offerId, quantity } = action.payload;
      return state.map(item => 
        item.offerId === offerId ? { ...item, quantity } : item
      );
    }
    case CLEAR_CART:
      return [];
    default:
      return state;
  }
};

// Create context
const CartContext = createContext();

// Utility hook
export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

// Provider component
export const CartProvider = ({ children }) => {
  const [cart, dispatch] = useReducer(cartReducer, []);
  
  // Methods for cart manipulation
  const addToCart = useCallback((offerId, offer, quantity = 1) => {
    if (quantity <= 0) return;
    
    dispatch({
      type: ADD_TO_CART,
      payload: { offerId, quantity, offer }
    });
  }, []);
  
  const removeFromCart = useCallback((offerId) => {
    dispatch({
      type: REMOVE_FROM_CART,
      payload: offerId
    });
  }, []);
  
  const updateQuantity = useCallback((offerId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(offerId);
      return;
    }
    
    dispatch({
      type: UPDATE_QUANTITY,
      payload: { offerId, quantity: Math.min(quantity, 20) }
    });
  }, [removeFromCart]);
  
  const clearCart = useCallback(() => {
    dispatch({ type: CLEAR_CART });
  }, []);
  
  // Load cart from localStorage on initialization
  useEffect(() => {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      try {
        const parsedCart = JSON.parse(savedCart);
        dispatch({ type: INIT_CART, payload: parsedCart });
      } catch (error) {
        console.error('Failed to parse cart from localStorage:', error);
      }
    }
  }, []);
  
  // Save cart to localStorage on every change
  useEffect(() => {
    localStorage.setItem('cart', JSON.stringify(cart));
  }, [cart]);
  
  // Listen for user logout event
  useEffect(() => {
    const handleLogout = () => {
      clearCart();
      localStorage.removeItem('cart');
    };
    
    window.addEventListener('user-logout', handleLogout);
    
    return () => {
      window.removeEventListener('user-logout', handleLogout);
    };
  }, [clearCart]);
  
  // Calculate total number of products in cart
  const totalItems = cart.reduce((total, item) => total + item.quantity, 0);
  
  // Calculate total cart value
  const totalValue = cart.reduce((total, item) => 
    total + (item.offer?.price || 0) * item.quantity, 0);
  
  // Context value
  const value = {
    cart,
    totalItems,
    totalValue,
    addToCart,
    removeFromCart,
    updateQuantity,
    clearCart
  };
  
  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};

CartProvider.propTypes = {
  children: PropTypes.node.isRequired
};

export default CartContext; 