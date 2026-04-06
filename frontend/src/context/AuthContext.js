import React, { createContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');

    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      setIsAuthenticated(true);
    }

    setLoading(false);
  }, []);

  const signup = async (credentials) => {
    try {
      const response = await authAPI.signup(credentials);
      console.log('Signup Response:', response.data);
      
      if (response.data.success) {
        return response.data;
      } else {
        throw new Error(response.data.message || 'Signup failed');
      }
    } catch (error) {
      console.error('Signup Error:', error.response?.data || error.message);
      throw error.response?.data || { message: error.message };
    }
  };

  const login = async (credentials) => {
    try {
      const response = await authAPI.login(credentials);
      console.log('Login Response:', response.data);
      
      // Check if response is successful
      if (!response.data.success) {
        throw new Error(response.data.message || 'Login failed');
      }

      // Extract token and user from response
      const { access_token, user } = response.data;

      if (!access_token) {
        throw new Error('No access token received');
      }

      if (!user) {
        throw new Error('No user data received');
      }

      // Save to localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      // Update state
      setToken(access_token);
      setUser(user);
      setIsAuthenticated(true);

      console.log('✅ Login successful, user:', user);
      return response.data;
    } catch (error) {
      console.error('Login Error:', error.response?.data || error.message);
      throw error.response?.data || { message: error.message };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
  };

  const getProfile = async () => {
    try {
      const response = await authAPI.getProfile();
      console.log('Profile Response:', response.data);
      
      if (response.data.success && response.data.data) {
        return response.data;
      } else {
        throw new Error('Failed to get profile');
      }
    } catch (error) {
      console.error('Get Profile Error:', error.response?.data || error.message);
      throw error.response?.data || { message: error.message };
    }
  };

  const updateProfile = async (data) => {
    try {
      const response = await authAPI.updateProfile(data);
      console.log('Update Profile Response:', response.data);
      
      if (response.data.success) {
        // Update local user data
        const updatedUser = { ...user, ...data };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        setUser(updatedUser);
        return response.data;
      } else {
        throw new Error(response.data.message || 'Update failed');
      }
    } catch (error) {
      console.error('Update Profile Error:', error.response?.data || error.message);
      throw error.response?.data || { message: error.message };
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated,
        signup,
        login,
        logout,
        getProfile,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};