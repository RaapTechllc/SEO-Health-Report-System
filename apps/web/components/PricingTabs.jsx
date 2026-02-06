import React, { useState, useEffect } from 'react';
import './PricingTabs.css';

const PricingTabs = () => {
  const [activeTab, setActiveTab] = useState('pro');
  const [pricingData, setPricingData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPricingData();
  }, []);

  const fetchPricingData = async () => {
    try {
      const response = await fetch('/tier-recommendation/tiers');
      const data = await response.json();
      setPricingData(data.tier_comparison);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch pricing data:', error);
      // Fallback data
      setPricingData({
        basic: {
          name: 'Basic',
          price: { monthly: 800, setup: 0 },
          features: ['Technical SEO audit', 'Basic recommendations', 'PDF report']
        },
        pro: {
          name: 'Pro',
          price: { monthly: 2500, setup: 500 },
          features: ['Complete SEO audit', 'AI visibility analysis', 'Competitive benchmarking', 'Branded reports']
        },
        enterprise: {
          name: 'Enterprise',
          price: { monthly: 6000, setup: 2000 },
          features: ['Comprehensive analysis', 'Custom branding', 'ROI projections', 'Executive presentations']
        }
      });
      setLoading(false);
    }
  };

  const handleTabClick = (tab) => {
    setActiveTab(tab);
  };

  if (loading) {
    return <div className="pricing-loading">Loading pricing information...</div>;
  }

  return (
    <div className="pricing-tabs">
      <div className="tab-navigation">
        {Object.keys(pricingData).map((tier) => (
          <button
            key={tier}
            className={`tab ${activeTab === tier ? 'active' : ''}`}
            onClick={() => handleTabClick(tier)}
          >
            {pricingData[tier].name}
            {tier === 'pro' && <span className="popular-badge">Popular</span>}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {pricingData[activeTab] && (
          <div className="pricing-card">
            <div className="pricing-header">
              <h3>{pricingData[activeTab].name}</h3>
              <div className="price">
                <span className="amount">${pricingData[activeTab].price.monthly.toLocaleString()}</span>
                <span className="period">/month</span>
              </div>
              {pricingData[activeTab].price.setup > 0 && (
                <div className="setup-fee">
                  + ${pricingData[activeTab].price.setup.toLocaleString()} setup
                </div>
              )}
            </div>

            <div className="features-list">
              <h4>What's Included:</h4>
              <ul>
                {pricingData[activeTab].features.map((feature, index) => (
                  <li key={index}>
                    <span className="checkmark">✓</span>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            <div className="cta-section">
              <button className="cta-button">
                Get Started with {pricingData[activeTab].name}
              </button>
              <p className="cta-subtitle">
                {activeTab === 'basic' && 'Perfect for small businesses'}
                {activeTab === 'pro' && 'Most popular choice'}
                {activeTab === 'enterprise' && 'For large organizations'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PricingTabs;
