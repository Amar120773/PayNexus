import { useState } from 'react';
import { Credentials, User } from '../../../types';
import { authApi } from '../services/authApi';

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(() => {
    const cached = localStorage.getItem('cf_user');
    return cached ? JSON.parse(cached) : null;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (creds: Credentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await authApi.login(creds);
      localStorage.setItem('cf_token', response.token);
      localStorage.setItem('cf_user', JSON.stringify(response.user));
      setUser(response.user);
      window.dispatchEvent(new Event('auth_login'));
      return response.user;
    } catch (err: any) {
      const msg = err.response?.data?.error || 'Failed to authenticate user';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (creds: Credentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await authApi.register(creds);
      localStorage.setItem('cf_token', response.token);
      localStorage.setItem('cf_user', JSON.stringify(response.user));
      setUser(response.user);
      window.dispatchEvent(new Event('auth_login'));
      return response.user;
    } catch (err: any) {
      const msg = err.response?.data?.error || 'Registration failed';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('cf_token');
    localStorage.removeItem('cf_user');
    setUser(null);
    window.dispatchEvent(new Event('auth_logout'));
  };

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    register,
    logout,
  };
};
