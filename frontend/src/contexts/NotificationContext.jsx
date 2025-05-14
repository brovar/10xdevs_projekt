import React, { createContext, useContext, useReducer, useCallback, useId } from 'react';
import PropTypes from 'prop-types';

// Typy powiadomień
export const NOTIFICATION_TYPES = {
  SUCCESS: 'success',
  ERROR: 'error',
  INFO: 'info',
  WARNING: 'warning',
};

// Akcje
const ADD_NOTIFICATION = 'ADD_NOTIFICATION';
const REMOVE_NOTIFICATION = 'REMOVE_NOTIFICATION';

// Reducer do zarządzania stanem powiadomień
const notificationReducer = (state, action) => {
  switch (action.type) {
    case ADD_NOTIFICATION:
      return [...state, action.payload];
    case REMOVE_NOTIFICATION:
      return state.filter((notification) => notification.id !== action.payload);
    default:
      return state;
  }
};

// Tworzenie kontekstu
const NotificationContext = createContext();

// Hook użytkowy
export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

// Komponent dostawcy (Provider)
export const NotificationProvider = ({ children }) => {
  const [notifications, dispatch] = useReducer(notificationReducer, []);
  
  // Funkcja do generowania unikatowego ID dla każdego powiadomienia
  const generateUniqueId = useCallback(() => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }, []);
  
  // Funkcje do dodawania różnych typów powiadomień
  const addNotification = useCallback((message, type, timeout = 5000) => {
    const id = generateUniqueId();
    
    dispatch({
      type: ADD_NOTIFICATION,
      payload: {
        id,
        message,
        type,
        timestamp: Date.now()
      }
    });
    
    // Automatyczne usuwanie powiadomienia po zadanym czasie
    if (timeout !== null) {
      setTimeout(() => {
        dispatch({
          type: REMOVE_NOTIFICATION,
          payload: id
        });
      }, timeout);
    }
    
    return id;
  }, [generateUniqueId]);
  
  const addSuccess = useCallback((message, timeout) => {
    return addNotification(message, NOTIFICATION_TYPES.SUCCESS, timeout);
  }, [addNotification]);
  
  const addError = useCallback((message, timeout) => {
    return addNotification(message, NOTIFICATION_TYPES.ERROR, timeout);
  }, [addNotification]);
  
  const addInfo = useCallback((message, timeout) => {
    return addNotification(message, NOTIFICATION_TYPES.INFO, timeout);
  }, [addNotification]);
  
  const addWarning = useCallback((message, timeout) => {
    return addNotification(message, NOTIFICATION_TYPES.WARNING, timeout);
  }, [addNotification]);
  
  // Funkcja do ręcznego usuwania powiadomienia
  const removeNotification = useCallback((id) => {
    dispatch({
      type: REMOVE_NOTIFICATION,
      payload: id
    });
  }, []);
  
  // Wartość kontekstu
  const value = {
    notifications,
    addSuccess,
    addError,
    addInfo,
    addWarning,
    removeNotification
  };
  
  return (
    <NotificationContext.Provider value={value}>
      {children}
      <ToastContainer notifications={notifications} removeNotification={removeNotification} />
    </NotificationContext.Provider>
  );
};

NotificationProvider.propTypes = {
  children: PropTypes.node.isRequired
};

// Komponent do wyświetlania powiadomień
const ToastContainer = ({ notifications, removeNotification }) => {
  const toastAreaId = useId();
  
  return (
    <div 
      className="toast-container position-fixed top-0 start-50 translate-middle-x p-3"
      style={{ zIndex: 1050 }}
      aria-live="polite"
      aria-atomic="true"
      id={toastAreaId}
    >
      {notifications.map((notification) => (
        <div 
          key={notification.id} 
          className={`toast show bg-${getBootstrapClass(notification.type)}`}
          role="alert" 
          aria-live="assertive" 
          aria-atomic="true"
        >
          <div className="toast-header">
            <strong className="me-auto">
              {getNotificationTitle(notification.type)}
            </strong>
            <button 
              type="button" 
              className="btn-close" 
              aria-label="Close"
              onClick={() => removeNotification(notification.id)}
            ></button>
          </div>
          <div className="toast-body text-white">
            {notification.message}
          </div>
        </div>
      ))}
    </div>
  );
};

ToastContainer.propTypes = {
  notifications: PropTypes.array.isRequired,
  removeNotification: PropTypes.func.isRequired
};

// Funkcje pomocnicze
const getBootstrapClass = (type) => {
  switch (type) {
    case NOTIFICATION_TYPES.SUCCESS:
      return 'success';
    case NOTIFICATION_TYPES.ERROR:
      return 'danger';
    case NOTIFICATION_TYPES.WARNING:
      return 'warning';
    case NOTIFICATION_TYPES.INFO:
      return 'info';
    default:
      return 'light';
  }
};

const getNotificationTitle = (type) => {
  switch (type) {
    case NOTIFICATION_TYPES.SUCCESS:
      return 'Success';
    case NOTIFICATION_TYPES.ERROR:
      return 'Error';
    case NOTIFICATION_TYPES.WARNING:
      return 'Warning';
    case NOTIFICATION_TYPES.INFO:
      return 'Information';
    default:
      return 'Notification';
  }
};

export default NotificationContext; 