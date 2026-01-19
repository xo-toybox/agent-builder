import { useState, useEffect, useCallback } from 'react';

const API_BASE = '/api/v1';

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/status`);
      const data = await response.json();
      setIsAuthenticated(data.authenticated);
      setUserEmail(data.email || null);
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
      setUserEmail(null);
    }
  }, []);

  const login = useCallback(() => {
    window.location.href = `${API_BASE}/auth/login`;
  }, []);

  const logout = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
      setIsAuthenticated(false);
      setUserEmail(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await checkAuth();
      setLoading(false);
    };
    init();
  }, [checkAuth]);

  return {
    isAuthenticated,
    userEmail,
    loading,
    login,
    logout,
    checkAuth,
  };
}
