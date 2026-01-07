// API Configuration for E-Frame Application
// Centralized configuration for all backend API endpoints

const API_BASE_URL = 'http://127.0.0.1:5000';

// API Endpoints Configuration
export const API_CONFIG = {
  // Base URL
  BASE_URL: API_BASE_URL,

  // Authentication APIs
  AUTH: {
    BASE: `${API_BASE_URL}/api/auth`,
    LOGIN: `${API_BASE_URL}/api/auth/login`,
    LOGOUT: `${API_BASE_URL}/api/auth/logout`,
    CHANGE_PASSWORD: `${API_BASE_URL}/api/auth/change-password`,
    VERIFY_TOKEN: `${API_BASE_URL}/api/auth/verify-token`,
  },

  // Camera Dashboard APIs
  CAMERA_DASHBOARD: {
    BASE: `${API_BASE_URL}/api/camera_dashboard`,
    
    // Live Detection APIs
    DETECTION_FEED: `${API_BASE_URL}/api/camera_dashboard/detection_feed`,
    GET_CAMERAS: `${API_BASE_URL}/api/camera_dashboard/cameras`,
    SAFETY_DETECTION: `${API_BASE_URL}/api/camera_dashboard/safetydetection`,
    STOP_DETECTION: `${API_BASE_URL}/api/camera_dashboard/stopdetection`,
    
    // File Analysis APIs - General Detection
    DEMO2_UPLOAD: `${API_BASE_URL}/api/camera_dashboard/demo2`,
    VIDEO_FEED2: `${API_BASE_URL}/api/camera_dashboard/video_feed2`,
    
    // File Analysis APIs - Zone-based Detection
    DEMO3_UPLOAD: `${API_BASE_URL}/api/camera_dashboard/demo3`,
    VIDEO_FEED3: `${API_BASE_URL}/api/camera_dashboard/video_feed3`,
    
    // File Analysis APIs - Class-based Detection
    DEMO4_UPLOAD: `${API_BASE_URL}/api/camera_dashboard/demo4`,
    VIDEO_FEED4: `${API_BASE_URL}/api/camera_dashboard/video_feed4`,
    
    // Video Processing Control APIs
    STOP_VIDEO_PROCESSING: `${API_BASE_URL}/api/camera_dashboard/stop_video_processing`,
    VIDEO_PROCESSING_STATUS: `${API_BASE_URL}/api/camera_dashboard/video_processing_status`,
  },

  // Camera Management APIs
  CAMERA_MANAGEMENT: {
    BASE: `${API_BASE_URL}/api/camera_management`,
    GET_ALL_CAMERAS: `${API_BASE_URL}/api/camera_management/cameras`,
    GET_CAMERA: `${API_BASE_URL}/api/camera_management/get_camera`,
    CREATE_CAMERA: `${API_BASE_URL}/api/camera_management/set_camera`,
    DELETE_CAMERA: `${API_BASE_URL}/api/camera_management/del_camera`,
  },


  // Employee Configuration APIs
  EMPLOYEE_CONFIGURATION: {
    BASE: `${API_BASE_URL}/api/employee_configuration`,
    
    // Employee Management APIs
    GET_ALL_EMPLOYEES: `${API_BASE_URL}/api/employee_configuration/employees`,
    DELETE_EMPLOYEE: `${API_BASE_URL}/api/employee_configuration/del_employee`,
    
    // Face Capture APIs (Legacy)
    CREATE_EMPLOYEE: `${API_BASE_URL}/api/employee_configuration/capture_faces`,
    
    // Face Capture APIs (New Streaming System)
    START_FACE_CAPTURE: `${API_BASE_URL}/api/employee_configuration/start_face_capture`,
    FACE_CAPTURE_FEED: `${API_BASE_URL}/api/employee_configuration/face_capture_feed`,
    FACE_CAPTURE_PROGRESS: `${API_BASE_URL}/api/employee_configuration/face_capture_progress`,
    STOP_FACE_CAPTURE: `${API_BASE_URL}/api/employee_configuration/stop_face_capture`,
  },


  // Main Dashboard APIs
  MAIN_DASHBOARD: {
    BASE: `${API_BASE_URL}/api/main_dashboard`,
    
    // Analytics and Visualization APIs
    EXCEPTION_PIECHART: `${API_BASE_URL}/api/main_dashboard/exception_piechart`,
    TREND_ANALYSIS: `${API_BASE_URL}/api/main_dashboard/trend_analysis`,
    BARGRAPH_USER_EXCEPTION_COUNTS: `${API_BASE_URL}/api/main_dashboard/bargraph-user-exception-counts`,
    EXCEPTION_HEATMAP: `${API_BASE_URL}/api/main_dashboard/exception-heatmap`,
    
    // Combined Data APIs
    COMBINED_EXCEPTION_DATA: `${API_BASE_URL}/api/main_dashboard/combined-exception-data`,
    
    // Report Generation APIs
    EXPORT_EXCEPTION_DATA: `${API_BASE_URL}/api/main_dashboard/export-exception-data`,
    DAILY_REPORT: `${API_BASE_URL}/api/main_dashboard/report`,
    
    // Legacy APIs (unused but available)
    LOGS_BY_DATE: `${API_BASE_URL}/api/main_dashboard/logs/by-date`,
  },

  // Model Management APIs
  MODEL_MANAGEMENT: {
    BASE: `${API_BASE_URL}/api/model_management`,
    
    // Model Data APIs
    GET_ALL_MODELS: `${API_BASE_URL}/api/model_management/models`,

  },

  // Model Mapping APIs
  MODEL_MAPPING: {
    BASE: `${API_BASE_URL}/api/model_mapping`,
    
    // Model CRUD APIs
    GET_MODEL: `${API_BASE_URL}/api/model_mapping/get_model`,
    CREATE_MODEL: `${API_BASE_URL}/api/model_mapping/set_model`,
    DELETE_MODEL: `${API_BASE_URL}/api/model_mapping/del_model`,
    
    // Camera-Model Linking APIs
    LINK_CAMERA_MODEL: `${API_BASE_URL}/api/model_mapping/link_camera_model`,
  },


  // Notification Management APIs
  NOTIFICATION_MANAGEMENT: {
    BASE: `${API_BASE_URL}/api/notification_management`,
    
    // Notification Data APIs
    GET_NOTIFICATIONS: `${API_BASE_URL}/api/notification_management/notifications`,
  },



  // Analytics APIs (from services)
  ANALYTICS: {
    BASE: `${API_BASE_URL}/api/analytics`,
    GET_DASHBOARD_DATA: `${API_BASE_URL}/api/analytics/dashboard`,
    GET_VIOLATIONS: `${API_BASE_URL}/api/analytics/violations`,
    GET_EMPLOYEES: `${API_BASE_URL}/api/analytics/employees`,
  },
};

// HTTP Methods Configuration
export const HTTP_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  DELETE: 'DELETE',
  PATCH: 'PATCH',
};

// Request Headers Configuration
export const REQUEST_HEADERS = {
  JSON: {
    'Content-Type': 'application/json',
  },
  FORM_DATA: {
    'Content-Type': 'multipart/form-data',
  },
  AUTH: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer', // Will be appended with token
  },
};

// API Response Status Codes
export const API_STATUS = {
  SUCCESS: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
};

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  SERVER_ERROR: 'Server error. Please try again later.',
  UNAUTHORIZED: 'Unauthorized access. Please login again.',
  NOT_FOUND: 'Resource not found.',
  BAD_REQUEST: 'Invalid request. Please check your input.',
  TIMEOUT: 'Request timeout. Please try again.',
};

// API Timeout Configuration
export const API_TIMEOUT = {
  DEFAULT: 10000, // 10 seconds
  UPLOAD: 30000,  // 30 seconds for file uploads
  LONG_REQUEST: 60000, // 60 seconds for long-running requests
};

// Helper Functions
export const API_HELPERS = {
  // Build URL with query parameters
  buildUrl: (baseUrl, params = {}) => {
    const url = new URL(baseUrl);
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined) {
        url.searchParams.append(key, params[key]);
      }
    });
    return url.toString();
  },

  // Build URL with path parameters
  buildPathUrl: (baseUrl, pathParams = {}) => {
    let url = baseUrl;
    Object.keys(pathParams).forEach(key => {
      url = url.replace(`{${key}}`, pathParams[key]);
    });
    return url;
  },

  // Get auth headers with token
  getAuthHeaders: (token) => ({
    ...REQUEST_HEADERS.JSON,
    'Authorization': `Bearer ${token}`,
  }),

  // Handle API response
  handleResponse: async (response) => {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  },

  // Make API request with error handling
  makeRequest: async (url, options = {}) => {
    try {
      const response = await fetch(url, {
        timeout: API_TIMEOUT.DEFAULT,
        ...options,
      });
      return await API_HELPERS.handleResponse(response);
    } catch (error) {
      console.error('API Request Error:', error);
      throw error;
    }
  },
};

// Export default configuration
export default API_CONFIG;
