import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === 'true';

export default function AuditForm({ onAnalyze, isLoading, setIsLoading }) {
  const [url, setUrl] = useState('');
  const [company, setCompany] = useState('');
  const [keywords, setKeywords] = useState('');
  const [tier, setTier] = useState('medium');
  const [error, setError] = useState('');

  const getSafeHostname = (urlStr) => {
    try {
      const normalizedUrl = urlStr.startsWith('http') ? urlStr : `https://${urlStr}`;
      return new URL(normalizedUrl).hostname;
    } catch (e) {
      return urlStr;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('Form submitted', { url, company, keywords });

    if (!url) {
      console.error('URL is missing');
      return;
    }

    setError('');
    if (setIsLoading) setIsLoading(true);

    if (DEMO_MODE) {
      try {
        const { mockReport } = await import('../mockData');
        onAnalyze(mockReport);
      } catch (err) {
        setError('Failed to load demo data');
      } finally {
        if (setIsLoading) setIsLoading(false);
      }
      return;
    }

    try {
      console.log('Sending request to:', `${API_URL}/audit`);

      // Basic validation
      if (!url.includes('.')) {
        throw new Error('Please enter a valid URL (e.g., example.com)');
      }

      // Start audit
      const response = await fetch(`${API_URL}/audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          company_name: company || getSafeHostname(url),
          keywords: keywords ? keywords.split(',').map(k => k.trim()) : [],
          competitors: [],
          tier: tier
        }),
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Server error:', errorText);
        throw new Error(`Failed to start audit: ${response.status} ${errorText}`);
      }

      const data = await response.json();
      console.log('Audit started:', data);
      const { audit_id } = data;

      // Poll for results
      let attempts = 0;
      const maxAttempts = 60; // 2 minutes max

      while (attempts < maxAttempts) {
        await new Promise(r => setTimeout(r, 2000));

        console.log(`Polling attempt ${attempts + 1}/${maxAttempts} for audit ${audit_id}...`);
        const statusRes = await fetch(`${API_URL}/audit/${audit_id}`);

        if (!statusRes.ok) {
          console.warn(`Poll failed: ${statusRes.status}`);
          continue;
        }

        const status = await statusRes.json();
        console.log('Poll status:', status.status);

        if (status.status === 'completed') {
          // Get full results
          console.log('Audit completed, fetching full results...');
          const fullRes = await fetch(`${API_URL}/audit/${audit_id}/full`);
          const fullData = await fullRes.json();
          onAnalyze(fullData);
          return;
        } else if (status.status === 'failed') {
          throw new Error('Audit failed on server');
        }

        attempts++;
      }

      throw new Error('Audit timed out');

    } catch (err) {
      console.error('Submission error:', err);
      setError(err.message || 'Failed to run audit');
      // Fall back to mock data for demo ONLY if explicit error
      // onAnalyze(url); 
    } finally {
      if (setIsLoading) setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto text-center px-4">
      <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6 tracking-tight">
        Check your <span className="text-brand-600">SEO Health</span> in seconds.
      </h1>
      <p className="text-lg text-slate-600 mb-8 max-w-lg mx-auto">
        Comprehensive analysis of your Technical SEO, Content Authority, and AI Visibility.
      </p>

      <form onSubmit={handleSubmit} className="max-w-lg mx-auto space-y-4">
        <div className="relative flex items-center">
          <Search className="absolute left-4 text-slate-400" size={20} aria-hidden="true" />
          <label htmlFor="website-url" className="sr-only">Website URL</label>
          <input
            id="website-url"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="example.com"
            className="w-full pl-12 pr-4 py-4 rounded-xl border border-slate-200 shadow-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-200 outline-none text-lg transition-all"
            required
            aria-required="true"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="company-name" className="sr-only">Company Name (optional)</label>
            <input
              id="company-name"
              type="text"
              value={company}
              onChange={(e) => setCompany(e.target.value)}
              placeholder="Company Name (optional)"
              className="w-full px-4 py-3 rounded-xl border border-slate-200 shadow-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-200 outline-none transition-all"
            />
          </div>
          <div>
            <label htmlFor="keywords" className="sr-only">Keywords (comma separated)</label>
            <input
              id="keywords"
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="Keywords (comma separated)"
              className="w-full px-4 py-3 rounded-xl border border-slate-200 shadow-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-200 outline-none transition-all"
            />
          </div>
        </div>

        {/* Tier Selection */}
        <fieldset>
          <legend className="sr-only">Select audit tier</legend>
          <div className="grid grid-cols-3 gap-3" role="radiogroup" aria-label="Audit tier selection">
            {[
              { id: 'low', label: 'Budget', desc: 'Fast Analysis' },
              { id: 'medium', label: 'Balanced', desc: 'Best Value' },
              { id: 'high', label: 'Premium', desc: 'Deep Dive' }
            ].map((option) => (
              <button
                key={option.id}
                type="button"
                role="radio"
                aria-checked={tier === option.id}
                onClick={() => setTier(option.id)}
                className={`py-3 px-2 rounded-xl border text-left transition-all focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 ${tier === option.id
                  ? 'bg-brand-50 border-brand-500 ring-1 ring-brand-500'
                  : 'border-slate-200 hover:border-brand-300'
                  }`}
              >
                <div className={`text-sm font-semibold ${tier === option.id ? 'text-brand-700' : 'text-slate-700'}`}>
                  {option.label}
                </div>
                <div className="text-xs text-slate-500 text-nowrap">
                  {option.desc}
                </div>
              </button>
            ))}
          </div>
        </fieldset>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-brand-600 hover:bg-brand-700 text-white py-4 rounded-xl font-semibold transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="animate-spin" size={20} aria-hidden="true" />
              <span>Analyzing... (this takes 1-2 minutes)</span>
            </>
          ) : (
            'Run Full SEO Audit'
          )}
        </button>

        {error && (
          <p className="text-red-500 text-sm" role="alert" aria-live="polite">{error}</p>
        )}
      </form>

      <div className="mt-8 flex justify-center gap-8 text-sm text-slate-400">
        <span className="flex items-center gap-2">✓ No credit card required</span>
        <span className="flex items-center gap-2">✓ Full PDF Report</span>
        <span className="flex items-center gap-2">✓ AI Analysis</span>
      </div>
    </div>
  );
}
