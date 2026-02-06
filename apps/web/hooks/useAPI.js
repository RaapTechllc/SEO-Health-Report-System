import { useState, useCallback } from 'react';

export const useAPI = (baseURL = '') => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const request = useCallback(async (endpoint, options = {}) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${baseURL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setLoading(false);
      return { data, error: null };
    } catch (err) {
      const errorMessage = err.message || 'An error occurred';
      setError(errorMessage);
      setLoading(false);
      return { data: null, error: errorMessage };
    }
  }, [baseURL]);

  const get = useCallback((endpoint, options = {}) => {
    return request(endpoint, { method: 'GET', ...options });
  }, [request]);

  const post = useCallback((endpoint, body, options = {}) => {
    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
      ...options
    });
  }, [request]);

  const retry = useCallback((lastRequest) => {
    if (lastRequest) {
      return lastRequest();
    }
  }, []);

  return {
    loading,
    error,
    get,
    post,
    retry,
    clearError: () => setError(null)
  };
};
