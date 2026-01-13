import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AuditForm from './components/AuditForm';
import ReportViewer from './components/ReportViewer';
import { DashboardShowcase } from './components/dashboard/DashboardShowcase';
import { ExecutiveBrief } from './components/dashboard/ExecutiveBrief';
import { mockReport } from './mockData';
import { Activity } from 'lucide-react';

function App() {
  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showDashboard, setShowDashboard] = useState(false);
  const [isMobileView, setIsMobileView] = useState(false);

  const handleAnalyze = (url) => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setReport({ ...mockReport, url }); // Inject the requested URL
      setIsLoading(false);
    }, 2000);
  };

  const handleReset = () => {
    setReport(null);
    setShowDashboard(false);
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-brand-100 selection:text-brand-900">
      {/* Header */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 cursor-pointer" onClick={handleReset}>
            <div className="bg-brand-600 text-white p-1.5 rounded-lg">
              <Activity size={20} />
            </div>
            <span className="font-bold text-xl tracking-tight">SEO Health</span>
          </div>
          <nav className="hidden md:flex gap-8 text-sm font-medium text-slate-500">
            <button 
              onClick={() => setShowDashboard(!showDashboard)}
              className="hover:text-brand-600 transition-colors"
            >
              {showDashboard ? 'Form View' : 'Dashboard'}
            </button>
            {showDashboard && (
              <button 
                onClick={() => setIsMobileView(!isMobileView)}
                className="hover:text-brand-600 transition-colors"
              >
                {isMobileView ? 'Desktop' : 'Mobile Brief'}
              </button>
            )}
            <a href="#" className="hover:text-brand-600 transition-colors">Features</a>
            <a href="#" className="hover:text-brand-600 transition-colors">Pricing</a>
            <a href="#" className="hover:text-brand-600 transition-colors">Docs</a>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-20">
        <AnimatePresence mode="wait">
          {showDashboard ? (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {isMobileView ? <ExecutiveBrief /> : <DashboardShowcase />}
            </motion.div>
          ) : !report ? (
            <motion.div 
              key="form"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col items-center justify-center min-h-[60vh]"
            >
              <AuditForm onAnalyze={handleAnalyze} isLoading={isLoading} />
            </motion.div>
          ) : (
            <motion.div
              key="report"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              <ReportViewer data={report} onReset={handleReset} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-100 py-12 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center text-slate-400 text-sm">
          <p>© 2024 SEO Health Report. Built for the modern web.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
