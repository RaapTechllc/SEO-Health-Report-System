import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Layout, FileText, Bot, Download, RefreshCw, AlertTriangle, Clock, Target } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/Tabs';
import { PillarCard } from './dashboard/PillarCard';
import IssuesList from './dashboard/IssuesList';
import { ActionCard } from './dashboard/ActionCard';
import { AIVisibilityPanel } from './dashboard/AIVisibilityPanel';
import { ScoreGauge } from './dashboard/ScoreGauge';
import { useAnimatedScore } from '../hooks/useAnimatedScore';
import { useTheme } from '../hooks/useTheme';
import { ExecutiveBrief } from './dashboard/ExecutiveBrief';

export default function ReportViewer({ data, onReset }) {
  const [activeTab, setActiveTab] = useState('overview');
  const [viewMode, setViewMode] = useState('technical');
  const animatedScore = useAnimatedScore(data?.overall_score || 0);

  // Apply custom branding color if present
  useTheme(data?.branding?.primaryColor);

  if (!data) return null;

  const pageVariants = {
    initial: { opacity: 0, y: 20 },
    in: { opacity: 1, y: 0 },
    out: { opacity: 0, y: -20 }
  };

  const pageTransition = {
    type: 'tween',
    ease: 'anticipate',
    duration: 0.5
  };

  // Map real data to Executive Brief format
  const executiveData = {
    aiVisibility: {
      score: data.component_scores?.ai_visibility?.score || 0,
      change: 0,
      trend: 'flat'
    },
    // Mock other metrics for main chart if needed, or pass through
    metrics: {
      technical: data.component_scores?.technical?.score || 0,
      content: data.component_scores?.content?.score || 0,
    },
    alerts: (data.critical_issues || []).map(issue => ({
      type: issue.type || 'technical',
      message: issue.description || issue.title,
      priority: 'high'
    })).slice(0, 3),
    competitive: data.competitive_analysis || []
  };

  return (
    <motion.div
      initial="initial"
      animate="in"
      exit="out"
      variants={pageVariants}
      transition={pageTransition}
      className="space-y-8"
    >
      {/* Header Actions */}
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex bg-slate-100 p-1 rounded-lg shadow-inner">
          <button
            onClick={() => setViewMode('executive')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${viewMode === 'executive' ? 'bg-white shadow text-brand-600' : 'text-slate-500 hover:text-slate-900'}`}
          >
            Executive Brief
          </button>
          <button
            onClick={() => { setViewMode('action'); setActiveTab('actions'); }}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${viewMode === 'action' ? 'bg-white shadow text-brand-600' : 'text-slate-500 hover:text-slate-900'}`}
          >
            Action Plan
          </button>
          <button
            onClick={() => setViewMode('technical')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${viewMode === 'technical' ? 'bg-white shadow text-brand-600' : 'text-slate-500 hover:text-slate-900'}`}
          >
            Technical Data
          </button>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onReset}
            className="text-slate-500 hover:text-slate-800 flex items-center gap-2 font-medium transition-colors"
          >
            <RefreshCw size={18} /> New Audit
          </button>
          <button className="bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 px-4 py-2 rounded-lg font-medium shadow-sm transition-all flex items-center gap-2">
            <Download size={18} /> PDF Report
          </button>
        </div>
      </div>

      {/* EXECUTIVE VIEW */}
      {viewMode === 'executive' && (
        <div className="max-w-4xl mx-auto">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 mb-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-slate-900">Executive Summary</h2>
              <div className="text-sm text-slate-500">
                generated for {data.company_name || 'Your Company'}
              </div>
            </div>

            <div className="prose prose-slate max-w-none text-slate-600 mb-8">
              <p className="text-lg leading-relaxed">
                Overall score: <strong>{data.overall_score}/100</strong>.
                {data.overall_score > 80
                  ? " Your digital presence is strong, but there are specific opportunities to dominate your market further."
                  : data.overall_score > 60
                    ? " Your foundation is decent, but critical gaps in AI visibility and technical SEO are preventing growth."
                    : " Significant issues are limiting your organic reach and AI visibility."}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="p-6 bg-slate-50 rounded-xl border border-slate-100">
                <div className="text-sm font-medium text-slate-500 mb-2 uppercase tracking-wide">Overall Health</div>
                <div className="text-4xl font-bold text-slate-900">{data.overall_score}</div>
                <div className={`mt-2 inline-flex items-center px-2 py-1 rounded text-xs font-semibold ${data.overall_score > 80 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                  {data.overall_score > 80 ? 'Healthy' : 'Needs Work'}
                </div>
              </div>
              <div className="p-6 bg-slate-50 rounded-xl border border-slate-100">
                <div className="text-sm font-medium text-slate-500 mb-2 uppercase tracking-wide">Critical Issues</div>
                <div className="text-4xl font-bold text-red-600">{data.critical_issues?.length || 0}</div>
                <div className="mt-2 text-sm text-slate-600">Blocking Growth</div>
              </div>
              <div className="p-6 bg-slate-50 rounded-xl border border-slate-100">
                <div className="text-sm font-medium text-slate-500 mb-2 uppercase tracking-wide">AI Share of Voice</div>
                <div className="text-4xl font-bold text-purple-600">{data.component_scores?.ai_visibility?.score || 0}%</div>
                <div className="mt-2 text-sm text-slate-600">Visibility in LLMs</div>
              </div>
            </div>

            <h3 className="text-lg font-bold text-slate-800 mb-4">Bottom Line Impact</h3>
            <ExecutiveBrief data={executiveData} />
          </div>
        </div>
      )}

      {/* ACTION PLAN VIEW */}
      {viewMode === 'action' && (
        <div className="max-w-5xl mx-auto">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Strategic Roadmap</h2>
            <p className="text-slate-600 mb-8">Prioritized actions to improve your search visibility over the next 3-6 months.</p>

            <div className="space-y-12">
              <section className="relative pl-8 border-l-2 border-red-200">
                <div className="absolute -left-2.5 top-0 bg-red-100 text-red-600 rounded-full p-1">
                  <AlertTriangle size={16} />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">
                  Phase 1: Immediate Fixes (Week 1-2)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(data.recommendations || []).filter(r => r.priority === 'high' || r.priority === 'critical').length > 0 ?
                    (data.recommendations || []).filter(r => r.priority === 'high' || r.priority === 'critical').map((rec, idx) => (
                      <ActionCard key={`high-${idx}`} recommendation={rec} />
                    )) : (
                      <div className="text-slate-500 italic p-4">No critical issues found. Great start!</div>
                    )
                  }
                </div>
              </section>

              <section className="relative pl-8 border-l-2 border-yellow-200">
                <div className="absolute -left-2.5 top-0 bg-yellow-100 text-yellow-600 rounded-full p-1">
                  <Clock size={16} />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">
                  Phase 2: Optimization (Month 1-2)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(data.recommendations || []).filter(r => r.priority === 'medium').length > 0 ?
                    (data.recommendations || []).filter(r => r.priority === 'medium').map((rec, idx) => (
                      <ActionCard key={`med-${idx}`} recommendation={rec} />
                    )) : (
                      <div className="text-slate-500 italic p-4">Focus on growth after Phase 1.</div>
                    )
                  }
                </div>
              </section>

              <section className="relative pl-8 border-l-2 border-blue-200">
                <div className="absolute -left-2.5 top-0 bg-blue-100 text-blue-600 rounded-full p-1">
                  <Target size={16} />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-4">
                  Phase 3: Strategic Growth (Month 3-6)
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(data.recommendations || []).filter(r => r.priority === 'low' || !r.priority).length > 0 ?
                    (data.recommendations || []).filter(r => r.priority === 'low' || !r.priority).map((rec, idx) => (
                      <ActionCard key={`low-${idx}`} recommendation={rec} />
                    )) : (
                      <div className="text-slate-500 italic p-4">Long-term strategy items.</div>
                    )
                  }
                </div>
              </section>
            </div>
          </div>
        </div>
      )}

      {/* TECHNICAL VIEW (Original) */}
      {viewMode === 'technical' && (
        <>
          {/* Hero Score Section */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
            <div className="flex flex-col md:flex-row items-center gap-8 md:gap-16">
              <div className="flex-shrink-0">
                <ScoreGauge score={animatedScore} grade={data.grade} label="Overall Score" className="border-0 shadow-none p-0" />
              </div>
              <div className="flex-1 text-center md:text-left">
                <div className="inline-block px-3 py-1 bg-slate-100 rounded-full text-slate-600 text-sm font-semibold mb-3">
                  Analyzed: {data.timestamp ? new Date(data.timestamp).toLocaleDateString() : new Date().toLocaleDateString()}
                </div>
                <h2 className="text-3xl font-bold text-slate-900 mb-2">
                  {data.grade === 'A' ? 'Excellent Work!' :
                    data.grade === 'B' ? 'Good, but room to grow.' :
                      data.grade === 'C' ? 'Needs Attention.' :
                        'Critical Improvements Needed.'}
                </h2>
                <p className="text-slate-600 text-lg">
                  Your overall SEO health score is <strong className="text-slate-900">{data.overall_score}/100</strong>.
                  We found <strong className="text-red-600">{data.critical_issues?.length || 0} critical issues</strong> that
                  are impacting your visibility.
                </p>
              </div>
            </div>
          </div>

          {/* Tabs Navigation */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-5">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="technical">Technical</TabsTrigger>
              <TabsTrigger value="content">Content</TabsTrigger>
              <TabsTrigger value="ai">AI Visibility</TabsTrigger>
              <TabsTrigger value="actions">Actions</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-8">
              {/* Pillars Grid - Responsive */}
              <motion.div
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2, staggerChildren: 0.1 }}
              >
                <PillarCard
                  pillar="technical"
                  data={data.component_scores?.technical || { score: 0, issues: [] }}
                  onViewAnalysis={() => setActiveTab('technical')}
                />
                <PillarCard
                  pillar="content"
                  data={data.component_scores?.content || { score: 0, issues: [] }}
                  onViewAnalysis={() => setActiveTab('content')}
                />
                <PillarCard
                  pillar="ai_visibility"
                  data={data.component_scores?.ai_visibility || { score: 0, issues: [] }}
                  onViewAnalysis={() => setActiveTab('ai')}
                />
              </motion.div>

              {/* Issues Overview */}
              <IssuesList
                issues={data.critical_issues || []}
                recommendations={data.recommendations?.slice(0, 6) || []}
              />
            </TabsContent>

            <TabsContent value="technical" className="space-y-6">
              <div className="bg-white rounded-xl p-6 border border-slate-100">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <Layout className="text-blue-600" size={24} />
                  Technical SEO Analysis
                </h3>
                <p className="text-slate-600 mb-6">
                  Score: <strong>{data.component_scores?.technical?.score || 0}/100</strong>
                </p>
                {/* Technical details would go here */}
                {data.audits?.technical && (
                  <pre className="bg-slate-50 p-4 rounded-lg overflow-auto text-xs">
                    {JSON.stringify(data.audits.technical, null, 2)}
                  </pre>
                )}
                {!data.audits?.technical && <div className="text-slate-500">Detailed technical analysis not available.</div>}
              </div>
            </TabsContent>

            <TabsContent value="content" className="space-y-6">
              <div className="bg-white rounded-xl p-6 border border-slate-100">
                <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <FileText className="text-green-600" size={24} />
                  Content & Authority Analysis
                </h3>
                <p className="text-slate-600 mb-6">
                  Score: <strong>{data.component_scores?.content?.score || 0}/100</strong>
                </p>
                {/* Content details would go here */}
                {data.audits?.content && (
                  <pre className="bg-slate-50 p-4 rounded-lg overflow-auto text-xs">
                    {JSON.stringify(data.audits.content, null, 2)}
                  </pre>
                )}
                {!data.audits?.content && <div className="text-slate-500">Detailed content analysis not available.</div>}
              </div>
            </TabsContent>

            <TabsContent value="ai" className="space-y-6">
              <AIVisibilityPanel data={data.component_scores?.ai_visibility || {}} />
            </TabsContent>

            <TabsContent value="actions" className="space-y-6">
              <div>
                <h3 className="text-2xl font-bold text-slate-900 mb-6">Action Plan</h3>
                <motion.div
                  className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ staggerChildren: 0.1 }}
                >
                  {(data.recommendations || []).map((rec, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: idx * 0.1 }}
                    >
                      <ActionCard
                        recommendation={rec}
                        onMarkComplete={(rec) => console.log('Mark complete:', rec)}
                        onLearnMore={(rec) => console.log('Learn more:', rec)}
                      />
                    </motion.div>
                  ))}
                </motion.div>
              </div>
            </TabsContent>
          </Tabs>
        </>
      )}
    </motion.div>
  );
}
