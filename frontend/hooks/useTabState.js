import { useState } from 'react';

export const useTabState = (defaultTab) => {
  const [state, setState] = useState({
    activeTab: defaultTab,
    tabHistory: [defaultTab],
    loading: false,
    error: null
  });

  const switchTab = (tab) => {
    setState(prev => ({
      ...prev,
      activeTab: tab,
      tabHistory: [...prev.tabHistory, tab],
      error: null
    }));
  };

  const setLoading = (loading) => {
    setState(prev => ({ ...prev, loading }));
  };

  const setError = (error) => {
    setState(prev => ({ ...prev, error }));
  };

  return { 
    ...state, 
    switchTab, 
    setLoading, 
    setError 
  };
};
