import React from 'react';
import { Activity } from 'lucide-react';

export function Footer() {
    return (
        <footer className="bg-white border-t border-slate-100 py-12" role="contentinfo">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2">
                        <div className="bg-slate-100 text-slate-500 p-1.5 rounded-lg" aria-hidden="true">
                            <Activity size={18} />
                        </div>
                        <span className="font-semibold text-slate-700">SEO Health</span>
                    </div>

                    <nav aria-label="Footer navigation" className="flex gap-8 text-sm text-slate-500">
                        <a href="#" className="hover:text-brand-600 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 rounded">Privacy</a>
                        <a href="#" className="hover:text-brand-600 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 rounded">Terms</a>
                        <a href="#" className="hover:text-brand-600 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 rounded" aria-label="Twitter (opens in new tab)">Twitter</a>
                        <a href="#" className="hover:text-brand-600 transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 rounded" aria-label="GitHub (opens in new tab)">GitHub</a>
                    </nav>

                    <div className="text-sm text-slate-400">
                        © {new Date().getFullYear()} SEO Health Report System
                    </div>
                </div>
            </div>
        </footer>
    );
}
