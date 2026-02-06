import { useState, useCallback } from 'react';

export const useURLCorrection = () => {
  const [validationState, setValidationState] = useState({
    isValid: false,
    correctedURL: '',
    corrections: [],
    error: null
  });

  const correctURL = useCallback((input) => {
    try {
      let corrected = input.trim();
      const corrections = [];

      // Add protocol if missing
      if (corrected && !corrected.match(/^https?:\/\//)) {
        corrected = `https://${corrected}`;
        corrections.push('Added HTTPS protocol');
      }

      // Add www if domain looks incomplete
      if (corrected.match(/^https?:\/\/[^.\/]+\.[^.\/]+$/)) {
        corrected = corrected.replace(/^(https?:\/\/)/, '$1www.');
        corrections.push('Added www subdomain');
      }

      // Remove trailing slash
      if (corrected.endsWith('/') && corrected.length > 8) {
        corrected = corrected.slice(0, -1);
        corrections.push('Removed trailing slash');
      }

      // Validate URL
      const isValid = validateURL(corrected);

      const result = {
        original: input,
        corrected,
        isValid,
        corrections,
        error: null
      };

      setValidationState(result);
      return result;
    } catch (error) {
      const errorResult = {
        original: input,
        corrected: input,
        isValid: false,
        corrections: [],
        error: 'Invalid URL format'
      };
      setValidationState(errorResult);
      return errorResult;
    }
  }, []);

  const validateURL = (url) => {
    try {
      const urlObj = new URL(url);
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const reset = () => {
    setValidationState({
      isValid: false,
      correctedURL: '',
      corrections: [],
      error: null
    });
  };

  return {
    ...validationState,
    correctURL,
    reset
  };
};
