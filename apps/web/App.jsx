import React, { useState } from 'react';
import PricingTabs from './components/PricingTabs';
import DocumentationTabs from './components/DocumentationTabs';
import URLInput from './components/URLInput';
import InteractivePricingCalculator from './components/InteractivePricingCalculator';
import './styles/App.css';

const App = () => {
  const [activeSection, setActiveSection] = useState('pricing');
  const [competitors, setCompetitors] = useState([]);

  const handleURLSubmit = (url) => {
    setCompetitors(prev => [...prev, { url, added: new Date() }]);
    console.log('Added competitor:', url);
  };

  const handleURLValidation = (validation) => {
    console.log('URL validation:', validation);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎯 OODA Loop Competitive Intelligence</h1>
        <nav className="main-nav">
          <button 
            className={activeSection === 'pricing' ? 'active' : ''}
            onClick={() => setActiveSection('pricing')}
          >
            Pricing
          </button>
          <button 
            className={activeSection === 'competitors' ? 'active' : ''}
            onClick={() => setActiveSection('competitors')}
          >
            Add Competitors
          </button>
          <button 
            className={activeSection === 'docs' ? 'active' : ''}
            onClick={() => setActiveSection('docs')}
          >
            Documentation
          </button>
        </nav>
      </header>

      <main className="app-main">
        {activeSection === 'pricing' && (
          <section className="pricing-section">
            <h2>Choose Your Plan</h2>
            <PricingTabs />
            <InteractivePricingCalculator />
          </section>
        )}

        {activeSection === 'competitors' && (
          <section className="competitors-section">
            <h2>Add Competitors for Monitoring</h2>
            <URLInput 
              onURLChange={handleURLSubmit}
              onValidation={handleURLValidation}
            />
            
            {competitors.length > 0 && (
              <div className="competitors-list">
                <h3>Added Competitors ({competitors.length})</h3>
                <ul>
                  {competitors.map((competitor, index) => (
                    <li key={index}>
                      <span className="competitor-url">{competitor.url}</span>
                      <span className="added-time">
                        Added: {competitor.added.toLocaleTimeString()}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        {activeSection === 'docs' && (
          <section className="docs-section">
            <DocumentationTabs />
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>🚀 Powered by OODA Loop System - Real-time competitive intelligence</p>
      </footer>
    </div>
  );
};

export default App;
