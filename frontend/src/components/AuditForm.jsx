import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

export default function AuditForm({ onAnalyze, isLoading }) {
  const [url, setUrl] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (url) onAnalyze(url);
  };

  return (
    <div className="w-full max-w-2xl mx-auto text-center px-4">
      <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6 tracking-tight">
        Check your <span className="text-brand-600">SEO Health</span> in seconds.
      </h1>
      <p className="text-lg text-slate-600 mb-8 max-w-lg mx-auto">
        Comprehensive analysis of your Technical SEO, Content Authority, and AI Visibility.
      </p>
      
      <form onSubmit={handleSubmit} className="relative max-w-lg mx-auto">
        <div className="relative flex items-center">
          <Search className="absolute left-4 text-slate-400" size={20} />
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://yourwebsite.com"
            className="w-full pl-12 pr-32 py-4 rounded-full border border-slate-200 shadow-sm focus:border-brand-500 focus:ring-2 focus:ring-brand-200 outline-none text-lg transition-all"
            required
          />
          <button
            type="submit"
            disabled={isLoading}
            className="absolute right-2 top-2 bottom-2 bg-brand-600 hover:bg-brand-700 text-white px-6 rounded-full font-semibold transition-colors disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading ? <Loader2 className="animate-spin" size={20} /> : 'Analyze'}
          </button>
        </div>
      </form>
      
      <div className="mt-8 flex justify-center gap-8 text-sm text-slate-400">
        <span className="flex items-center gap-2">✓ No credit card required</span>
        <span className="flex items-center gap-2">✓ Full PDF Report</span>
        <span className="flex items-center gap-2">✓ AI Analysis</span>
      </div>
    </div>
  );
}
