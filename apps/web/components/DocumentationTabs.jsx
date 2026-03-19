import React, { useState, useEffect } from 'react';
import './DocumentationTabs.css';

const DocumentationTabs = () => {
  const [activeTab, setActiveTab] = useState('api');
  const [searchTerm, setSearchTerm] = useState('');
  const [docContent, setDocContent] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDocumentation();
  }, []);

  const loadDocumentation = () => {
    // Mock documentation data - in production, this would come from API
    const mockDocs = {
      api: {
        title: 'API Reference',
        sections: [
          {
            id: 'authentication',
            title: 'Authentication',
            content: 'All API requests require authentication using Bearer tokens.',
            codeExamples: [
              {
                language: 'curl',
                code: `curl -H "Authorization: Bearer YOUR_API_KEY" \\
  https://api.ooda-system.com/competitors`,
                description: 'Example API call with authentication'
              },
              {
                language: 'javascript',
                code: `const response = await fetch('/competitors', {
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  }
});`,
                description: 'JavaScript fetch example'
              }
            ]
          },
          {
            id: 'competitors',
            title: 'Competitors API',
            content: 'Manage competitor monitoring and analysis.',
            codeExamples: [
              {
                language: 'json',
                code: `{
  "url": "https://competitor.com",
  "company_name": "Competitor Inc",
  "monitoring_frequency": 60,
  "alert_threshold": 10
}`,
                description: 'Add competitor request body'
              }
            ]
          }
        ]
      },
      guides: {
        title: 'Getting Started Guides',
        sections: [
          {
            id: 'quickstart',
            title: 'Quick Start Guide',
            content: 'Get up and running with the OODA Loop system in 5 minutes.',
            codeExamples: [
              {
                language: 'bash',
                code: `# 1. Set your API key
export OODA_API_KEY="your-api-key"

# 2. Add your first competitor
curl -X POST https://api.ooda-system.com/competitors \\
  -H "Authorization: Bearer $OODA_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://competitor.com", "company_name": "Competitor"}'`,
                description: 'Quick setup commands'
              }
            ]
          },
          {
            id: 'monitoring',
            title: 'Setting Up Monitoring',
            content: 'Configure real-time competitor monitoring and alerts.',
            codeExamples: []
          }
        ]
      },
      examples: {
        title: 'Code Examples',
        sections: [
          {
            id: 'competitive-analysis',
            title: 'Competitive Analysis',
            content: 'Generate automated competitive analysis and battlecards.',
            codeExamples: [
              {
                language: 'python',
                code: `import requests

# Generate competitive analysis
response = requests.post(
    'https://api.ooda-system.com/competitive-analysis/',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={
        'prospect_url': 'https://your-site.com',
        'competitor_urls': [
            'https://competitor1.com',
            'https://competitor2.com'
        ]
    }
)

analysis = response.json()
print(f"Win probability: {analysis['analysis']['win_probability']}")`,
                description: 'Python competitive analysis example'
              }
            ]
          }
        ]
      }
    };

    setDocContent(mockDocs);
    setLoading(false);
  };

  const handleTabClick = (tab) => {
    setActiveTab(tab);
    setSearchTerm('');
  };

  const copyToClipboard = (code) => {
    navigator.clipboard.writeText(code).then(() => {
      // Could add a toast notification here
      console.log('Code copied to clipboard');
    });
  };

  const filteredSections = docContent[activeTab]?.sections.filter(section =>
    searchTerm === '' || 
    section.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    section.content.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (loading) {
    return <div className="docs-loading">Loading documentation...</div>;
  }

  return (
    <div className="documentation-tabs">
      <div className="tab-navigation">
        <button
          className={`tab ${activeTab === 'api' ? 'active' : ''}`}
          onClick={() => handleTabClick('api')}
        >
          API Reference
        </button>
        <button
          className={`tab ${activeTab === 'guides' ? 'active' : ''}`}
          onClick={() => handleTabClick('guides')}
        >
          Guides
        </button>
        <button
          className={`tab ${activeTab === 'examples' ? 'active' : ''}`}
          onClick={() => handleTabClick('examples')}
        >
          Examples
        </button>
      </div>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search documentation..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="tab-content">
        <h2>{docContent[activeTab]?.title}</h2>
        
        {filteredSections.map((section) => (
          <div key={section.id} className="doc-section">
            <h3>{section.title}</h3>
            <p>{section.content}</p>
            
            {section.codeExamples?.map((example, index) => (
              <div key={index} className="code-example">
                <div className="code-header">
                  <span className="language-tag">{example.language}</span>
                  <button
                    className="copy-button"
                    onClick={() => copyToClipboard(example.code)}
                  >
                    Copy
                  </button>
                </div>
                <pre className="code-block">
                  <code>{example.code}</code>
                </pre>
                {example.description && (
                  <p className="code-description">{example.description}</p>
                )}
              </div>
            ))}
          </div>
        ))}

        {filteredSections.length === 0 && searchTerm && (
          <div className="no-results">
            No documentation found for "{searchTerm}"
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentationTabs;
