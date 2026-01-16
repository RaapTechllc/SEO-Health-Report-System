import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function AuditForm({ onAnalyze, isLoading, setIsLoading }) {
  const [url, setUrl] = useState('');
  const [company, setCompany] = useState('');
  const [keywords, setKeywords] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('Form submitted', { url, company, keywords });
    
    if (!url) {
      console.error('URL is missing');
      return;
    }
    
    setError('');
    if (setIsLoading) setIsLoading(true);
    
    try {
      console.log('Sending request to:', `${API_URL}/audit`);
      // Start audit
      const response = await fetch(`${API_URL}/audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url,
          company_name: company || new URL(url).hostname,
          keywords: keywords ? keywords.split(',').map(k => k.trim()) : [],
          competitors: [],
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
          <Search className="absolute left-4 text-slate-400" size={20} />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://yourwebsite.com"
            className="w-full pl-12 pr-4 py-4 rounded-xl border border-slate-200 shadow-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-200 outline-none text-lg transition-all"
            required
          />
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            placeholder="Company Name (optional)"
            className="w-full px-4 py-3 rounded-xl border border-slate-200 shadow-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-200 outline-none transition-all"
          />
          <input
            type="text"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder="Keywords (comma separated)"
            className="w-full px-4 py-3 rounded-xl border border-slate-200 shadow-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-200 outline-none transition-all"
          />
        </div>
        
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-brand-600 hover:bg-brand-700 text-white py-4 rounded-xl font-semibold transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Analyzing... (this takes 1-2 minutes)
            </>
          ) : (
            'Run Full SEO Audit'
          )}
        </button>
        
        {error && (
          <p className="text-red-500 text-sm">{error}</p>
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
