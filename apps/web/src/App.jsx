import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import AuditForm from './components/AuditForm';
import ReportViewer from './components/ReportViewer';
import { DashboardShowcase } from './components/dashboard/DashboardShowcase';
import { ExecutiveBrief } from './components/dashboard/ExecutiveBrief';
import { Features } from './components/pages/Features';
import { Pricing } from './components/pages/Pricing';
import { Docs } from './components/pages/Docs';
function HomePage({ report, setReport, isLoading, setIsLoading }) {
  const handleAnalyze = (data) => {
    setReport(data);
    setIsLoading(false);
  };

  const handleReset = () => {
    setReport(null);
  };

  if (report) {
    return (
      <motion.div
        key="report"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
      >
        <ReportViewer data={report} onReset={handleReset} />
      </motion.div>
    );
  }

  return (
    <motion.div
      key="hero"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.5 }}
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center justify-center min-h-[70vh] text-center"
    >
      <div className="space-y-6 max-w-3xl">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-50 border border-brand-100 text-brand-600 text-sm font-medium mb-4">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-500"></span>
          </span>
          AI-Powered Analytics 2.0
        </div>

        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-slate-900">
          How does AI <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-600 to-ai-600">see your brand?</span>
        </h1>

        <p className="text-xl text-slate-500 max-w-2xl mx-auto leading-relaxed">
          Get a comprehensive health report that analyzes your technical SEO, content strategy, and visibility across AI search engines like ChatGPT and Claude.
        </p>

        <div className="pt-8 w-full max-w-md mx-auto">
          <AuditForm onAnalyze={handleAnalyze} isLoading={isLoading} setIsLoading={setIsLoading} />
        </div>

        <p className="text-sm text-slate-400 mt-8">
          Analyzed 10,000+ websites • No credit card required
        </p>
      </div>
    </motion.div>
  );
}

function DashboardPage({ isMobileView }) {
  return (
    <motion.div
      key="dashboard"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"
    >
      {isMobileView ? <ExecutiveBrief /> : <DashboardShowcase />}
    </motion.div>
  );
}

function AnimatedPage({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
    >
      {children}
    </motion.div>
  );
}

function AppContent() {
  const [report, setReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isMobileView] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-brand-100 selection:text-brand-900 flex flex-col">
      <Header branding={report?.branding} />

      <main className="flex-grow pt-24 pb-20">
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route
              path="/"
              element={
                <HomePage
                  report={report}
                  setReport={setReport}
                  isLoading={isLoading}
                  setIsLoading={setIsLoading}
                />
              }
            />
            <Route
              path="/dashboard"
              element={<DashboardPage isMobileView={isMobileView} />}
            />
            <Route
              path="/features"
              element={<AnimatedPage><Features /></AnimatedPage>}
            />
            <Route
              path="/pricing"
              element={<AnimatedPage><Pricing /></AnimatedPage>}
            />
            <Route
              path="/docs"
              element={<AnimatedPage><Docs /></AnimatedPage>}
            />
            <Route
              path="/report/:id"
              element={
                <motion.div
                  key="report"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                >
                  <ReportViewer data={report} onReset={() => navigate('/')} />
                </motion.div>
              }
            />
          </Routes>
        </AnimatePresence>
      </main>

      <Footer />
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
