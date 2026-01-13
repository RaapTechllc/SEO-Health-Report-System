import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Layout, FileText, Bot, Download, RefreshCw } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/Tabs';
import { PillarCard } from './dashboard/PillarCard';
import IssuesList from './dashboard/IssuesList';
import { ActionCard } from './dashboard/ActionCard';
import { AIVisibilityPanel } from './dashboard/AIVisibilityPanel';
import ScoreRadial from './charts/ScoreRadial';
import { useAnimatedScore } from '../hooks/useAnimatedScore';

export default function ReportViewer({ data, onReset }) {
  const [activeTab, setActiveTab] = useState('overview');
  const animatedScore = useAnimatedScore(data?.overall_score || 0);

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
      <div className="flex justify-between items-center">
        <button 
          onClick={onReset}
          className="text-slate-500 hover:text-slate-800 flex items-center gap-2 font-medium transition-colors"
        >
          <RefreshCw size={18} /> Run New Audit
        </button>
        <button className="bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 px-4 py-2 rounded-lg font-medium shadow-sm transition-all flex items-center gap-2">
          <Download size={18} /> Export PDF
        </button>
      </div>

      {/* Hero Score Section */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        <div className="flex flex-col md:flex-row items-center gap-8 md:gap-16">
          <div className="flex-shrink-0">
            <ScoreRadial score={animatedScore} size={120} />
          </div>
          <div className="flex-1 text-center md:text-left">
            <div className="inline-block px-3 py-1 bg-slate-100 rounded-full text-slate-600 text-sm font-semibold mb-3">
              Analyzed: {new Date(data.timestamp).toLocaleDateString()}
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
            <div className="text-slate-500">Detailed technical analysis coming soon...</div>
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
            <div className="text-slate-500">Detailed content analysis coming soon...</div>
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
    </motion.div>
  );
}
