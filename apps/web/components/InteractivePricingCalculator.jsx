import React, { useState, useEffect } from 'react';
import { useAPI } from '../hooks/useAPI';
import './InteractivePricingCalculator.css';

const InteractivePricingCalculator = () => {
  const [siteData, setSiteData] = useState({
    url: '',
    estimatedPages: 500,
    domainAuthority: 40,
    budgetRange: '2000-5000',
    industry: 'general',
    urgency: 'medium'
  });
  
  const [recommendation, setRecommendation] = useState(null);
  const { loading, error, post } = useAPI();

  const handleInputChange = (field, value) => {
    setSiteData(prev => ({ ...prev, [field]: value }));
  };

  const calculateRecommendation = async () => {
    if (!siteData.url) return;

    const { data, error } = await post('/tier-recommendation/', {
      target_url: siteData.url,
      budget_range: siteData.budgetRange,
      custom_requirements: {
        budget_max: parseInt(siteData.budgetRange.split('-')[1]),
        timeline_days: siteData.urgency === 'high' ? 3 : siteData.urgency === 'medium' ? 7 : 14
      },
      market_context: {
        industry: siteData.industry,
        urgency: siteData.urgency
      }
    });

    if (data) {
      setRecommendation(data);
    }
  };

  useEffect(() => {
    if (siteData.url) {
      const debounceTimer = setTimeout(calculateRecommendation, 1000);
      return () => clearTimeout(debounceTimer);
    }
  }, [siteData]);

  return (
    <div className="pricing-calculator">
      <h3>Interactive Pricing Calculator</h3>
      
      <div className="calculator-form">
        <div className="form-group">
          <label>Website URL</label>
          <input
            type="text"
            value={siteData.url}
            onChange={(e) => handleInputChange('url', e.target.value)}
            placeholder="https://your-website.com"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Budget Range</label>
            <select
              value={siteData.budgetRange}
              onChange={(e) => handleInputChange('budgetRange', e.target.value)}
            >
              <option value="500-1500">$500 - $1,500</option>
              <option value="1500-4000">$1,500 - $4,000</option>
              <option value="4000-10000">$4,000 - $10,000</option>
              <option value="10000+">$10,000+</option>
            </select>
          </div>

          <div className="form-group">
            <label>Industry</label>
            <select
              value={siteData.industry}
              onChange={(e) => handleInputChange('industry', e.target.value)}
            >
              <option value="general">General</option>
              <option value="finance">Finance</option>
              <option value="healthcare">Healthcare</option>
              <option value="legal">Legal</option>
              <option value="ecommerce">E-commerce</option>
              <option value="saas">SaaS</option>
            </select>
          </div>
        </div>

        <div className="form-group">
          <label>Project Urgency</label>
          <div className="radio-group">
            {['low', 'medium', 'high'].map(urgency => (
              <label key={urgency} className="radio-label">
                <input
                  type="radio"
                  name="urgency"
                  value={urgency}
                  checked={siteData.urgency === urgency}
                  onChange={(e) => handleInputChange('urgency', e.target.value)}
                />
                {urgency.charAt(0).toUpperCase() + urgency.slice(1)}
              </label>
            ))}
          </div>
        </div>
      </div>

      {loading && <div className="loading">Calculating recommendation...</div>}
      
      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}

      {recommendation && (
        <div className="recommendation-result">
          <h4>Recommended Tier: {recommendation.tier_recommendation.recommended_tier}</h4>
          
          <div className="pricing-details">
            <div className="price-box">
              <span className="price">
                ${recommendation.pricing_optimization.recommended_pricing.recommended.toLocaleString()}
              </span>
              <span className="period">/project</span>
            </div>
            
            <div className="roi-info">
              <p>Estimated ROI: {recommendation.pricing_optimization.value_proposition.roi_multiple.toFixed(1)}x</p>
              <p>Payback Period: {Math.round(recommendation.pricing_optimization.value_proposition.payback_period_months)} months</p>
            </div>
          </div>

          <div className="confidence-score">
            Confidence: {Math.round(recommendation.tier_recommendation.confidence * 100)}%
          </div>

          <div className="reasoning">
            <h5>Why this tier?</h5>
            <ul>
              {recommendation.tier_recommendation.reasoning.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default InteractivePricingCalculator;
