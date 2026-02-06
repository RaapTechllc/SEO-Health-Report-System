import React, { useState, useEffect } from 'react';
import './URLInput.css';

const URLInput = ({ onURLChange, onValidation }) => {
  const [url, setUrl] = useState('');
  const [correctedURL, setCorrectedURL] = useState('');
  const [validationStatus, setValidationStatus] = useState('');
  const [corrections, setCorrections] = useState([]);
  const [isValid, setIsValid] = useState(false);

  const correctURL = (input) => {
    let corrected = input.trim();
    const correctionsList = [];

    // Add protocol if missing
    if (corrected && !corrected.match(/^https?:\/\//)) {
      corrected = `https://${corrected}`;
      correctionsList.push('Added HTTPS protocol');
    }

    // Add www if domain looks incomplete (simple heuristic)
    if (corrected.match(/^https?:\/\/[^.\/]+\.[^.\/]+$/)) {
      corrected = corrected.replace(/^(https?:\/\/)/, '$1www.');
      correctionsList.push('Added www subdomain');
    }

    // Remove trailing slash
    if (corrected.endsWith('/') && corrected !== 'https://' && corrected !== 'http://') {
      corrected = corrected.slice(0, -1);
      correctionsList.push('Removed trailing slash');
    }

    // Validate URL format
    const isValidURL = validateURL(corrected);

    return {
      original: input,
      corrected,
      isValid: isValidURL,
      corrections: correctionsList
    };
  };

  const validateURL = (url) => {
    try {
      const urlObj = new URL(url);
      return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
    } catch {
      return false;
    }
  };

  const handleURLChange = (e) => {
    const inputValue = e.target.value;
    setUrl(inputValue);

    if (inputValue.trim()) {
      const validation = correctURL(inputValue);
      setCorrectedURL(validation.corrected);
      setCorrections(validation.corrections);
      setIsValid(validation.isValid);
      
      if (validation.isValid) {
        setValidationStatus('valid');
      } else {
        setValidationStatus('invalid');
      }
    } else {
      setCorrectedURL('');
      setCorrections([]);
      setIsValid(false);
      setValidationStatus('');
    }
  };

  const handleBlur = () => {
    if (url.trim() && correctedURL && isValid) {
      setUrl(correctedURL);
      if (onURLChange) {
        onURLChange(correctedURL);
      }
    }
    if (onValidation) {
      onValidation({ isValid, correctedURL, corrections });
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isValid && onURLChange) {
      onURLChange(correctedURL);
    }
  };

  return (
    <div className="url-input-container">
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <input
            type="text"
            className={`url-input ${validationStatus}`}
            value={url}
            onChange={handleURLChange}
            onBlur={handleBlur}
            placeholder="Enter competitor URL (e.g., example.com)"
          />
          <button 
            type="submit" 
            className="submit-button"
            disabled={!isValid}
          >
            Add Competitor
          </button>
        </div>

        {correctedURL && correctedURL !== url && (
          <div className="url-preview">
            <span className="preview-label">Corrected URL:</span>
            <span className="preview-url">{correctedURL}</span>
          </div>
        )}

        {corrections.length > 0 && (
          <div className="corrections-list">
            <span className="corrections-label">Auto-corrections applied:</span>
            <ul>
              {corrections.map((correction, index) => (
                <li key={index}>{correction}</li>
              ))}
            </ul>
          </div>
        )}

        {validationStatus === 'invalid' && url.trim() && (
          <div className="validation-message error">
            Please enter a valid URL format
          </div>
        )}

        {validationStatus === 'valid' && (
          <div className="validation-message success">
            ✓ Valid URL format
          </div>
        )}
      </form>
    </div>
  );
};

export default URLInput;
