import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle, ChevronDown, AlertCircle, Info } from 'lucide-react';
import { Badge } from '../ui/Badge';
import Accordion from '../ui/Accordion';

const severityConfig = {
  critical: { color: 'red', icon: AlertTriangle },
  high: { color: 'orange', icon: AlertCircle },
  medium: { color: 'yellow', icon: Info },
  low: { color: 'blue', icon: Info }
};

export default function IssuesList({ issues, recommendations }) {
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  const issueItems = issues.map((issue, idx) => {
    const severity = issue.severity || 'medium';
    const config = severityConfig[severity];
    const Icon = config.icon;

    return {
      title: (
        <div className="flex items-center gap-3">
          <Icon size={16} className={`text-${config.color}-600`} />
          <span>{issue.description}</span>
          <Badge variant={config.color} size="sm">{severity}</Badge>
        </div>
      ),
      content: (
        <div className="space-y-2">
          <p className="text-sm text-slate-600">{issue.details || 'No additional details available.'}</p>
          <div className="text-xs text-slate-500">
            Component: <span className="font-medium">{issue.component}</span>
          </div>
        </div>
      )
    };
  });

  const recommendationItems = recommendations.map((rec, idx) => ({
    title: (
      <div className="flex items-center justify-between w-full">
        <span>{rec.action}</span>
        <div className="flex gap-2">
          {rec.priority === 'quick_win' && (
            <Badge variant="green" size="sm">Quick Win</Badge>
          )}
          {rec.priority === 'high' && (
            <Badge variant="orange" size="sm">High Impact</Badge>
          )}
        </div>
      </div>
    ),
    content: (
      <div className="space-y-3">
        <p className="text-sm text-slate-600">{rec.details}</p>
        <div className="flex gap-4 text-xs text-slate-500">
          <span>Impact: <span className="capitalize font-medium text-slate-700">{rec.impact}</span></span>
          <span>Effort: <span className="capitalize font-medium text-slate-700">{rec.effort}</span></span>
        </div>
      </div>
    )
  }));

  return (
    <motion.div 
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 lg:grid-cols-2 gap-8"
    >
      {/* Critical Issues */}
      <motion.div variants={item} className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-red-50 flex items-center gap-2">
          <AlertTriangle className="text-red-600" size={20} />
          <h3 className="font-semibold text-red-900">Critical Issues</h3>
          <Badge variant="red" size="sm">{issues.length}</Badge>
        </div>
        <div className="p-4">
          {issues.length > 0 ? (
            <Accordion items={issueItems} />
          ) : (
            <div className="py-8 text-center text-slate-500">
              <CheckCircle className="mx-auto mb-2 text-green-500" size={32} />
              No critical issues found! 🎉
            </div>
          )}
        </div>
      </motion.div>

      {/* Recommendations */}
      <motion.div variants={item} className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-green-50 flex items-center gap-2">
          <CheckCircle className="text-green-600" size={20} />
          <h3 className="font-semibold text-green-900">Recommended Actions</h3>
          <Badge variant="green" size="sm">{recommendations.length}</Badge>
        </div>
        <div className="p-4">
          <Accordion items={recommendationItems} />
        </div>
      </motion.div>
    </motion.div>
  );
}