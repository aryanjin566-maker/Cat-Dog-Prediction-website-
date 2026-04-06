import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

console.log('🔌 API URL:', API_URL);

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Log all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('✅ Token added to request');
    }
    
    console.log('📤 Request:', {
      method: config.method.toUpperCase(),
      url: config.baseURL + config.url,
      data: config.data,
    });
    
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor - Log all responses
apiClient.interceptors.response.use(
  (response) => {
    console.log('📥 Response Success:', {
      status: response.status,
      url: response.config.url,
      data: response.data,
    });
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', {
      status: error.response?.status,
      url: error.response?.config?.url,
      data: error.response?.data,
      message: error.message,
    });

    // Handle 401 - Unauthorized
    if (error.response?.status === 401) {
      console.warn('⚠️ Token expired or invalid');
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

// ============================================================================
// AUTH API - Format: { email, password }
// ============================================================================

export const authAPI = {
  signup: (data) => {
    // Send exactly as backend expects
    const payload = {
      username: data.username,
      email: data.email.toLowerCase(),
      password: data.password,
      name: data.name,
      phone_number: data.phone_number || null,
      address: data.address || null,
    };
    console.log('📝 Signup payload:', payload);
    return apiClient.post('/api/auth/signup', payload);
  },

  login: (data) => {
    // Send exactly as backend expects
    const payload = {
      email: data.email.toLowerCase(),
      password: data.password,
    };
    console.log('🔐 Login payload:', payload);
    return apiClient.post('/api/auth/login', payload);
  },

  getProfile: () => {
    console.log('👤 Getting profile...');
    return apiClient.get('/api/auth/profile');
  },

  updateProfile: (data) => {
    // Only send fields that were provided
    const payload = {};
    if (data.name) payload.name = data.name;
    if (data.phone_number) payload.phone_number = data.phone_number;
    if (data.address) payload.address = data.address;
    
    console.log('✏️ Update profile payload:', payload);
    return apiClient.put('/api/auth/profile/update', payload);
  },
};

// ============================================================================
// PREDICTION API - Format: FormData for files, JSON for others
// ============================================================================

export const predictAPI = {
  uploadImages: (files) => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    console.log('📤 Uploading', files.length, 'images...');
    
    return apiClient.post('/api/predict/upload-and-predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  getHistory: (limit = 50, offset = 0) => {
    const payload = { limit, offset };
    console.log('📜 Getting history:', payload);
    return apiClient.post('/api/predict/history', payload);
  },

  getImage: (imageId) => {
    const payload = { image_id: imageId };
    console.log('🖼️ Getting image:', payload);
    return apiClient.post('/api/predict/get-image', payload);
  },

  deleteImage: (imageId) => {
    const payload = { image_id: imageId };
    console.log('🗑️ Deleting image:', payload);
    return apiClient.post('/api/predict/delete-image', payload);
  },
};

// ============================================================================
// HEALTH CHECK
// ============================================================================

export const healthAPI = {
  check: () => {
    console.log('🏥 Health check...');
    return apiClient.get('/api/health');
  },
};

export default apiClient;