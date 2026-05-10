import axios from 'axios';
import config from '../config';

const api = axios.create({
  baseURL: config.apiBaseUrl,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor
api.interceptors.request.use(
  (request) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API] ${request.method.toUpperCase()} ${request.url}`);
    }
    return request;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error normalization
api.interceptors.response.use(
  (response) => response,
  (error) => {
    let normalizedError = {
      error: true,
      error_code: 'UNKNOWN_ERROR',
      message: 'An unknown error occurred.',
      details: null
    };

    if (error.response && error.response.data && error.response.data.error_code) {
      normalizedError = { ...error.response.data };
    } else if (error.request) {
      normalizedError = {
        error: true,
        error_code: 'NETWORK_ERROR',
        message: 'Could not connect to the server. Please check your network connection.',
        details: null
      };
    } else {
      normalizedError.message = error.message;
    }
    
    // Always return a rejected promise with the normalized error
    return Promise.reject(normalizedError);
  }
);

export default api;
