import React from 'react';
import { AlertTriangle, CheckCircle, ArrowRight } from 'lucide-react';

export default function IssuesList({ issues, recommendations }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Critical Issues */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-red-50 flex items-center gap-2">
          <AlertTriangle className="text-red-600" size={20} />
          <h3 className="font-semibold text-red-900">Critical Issues</h3>
        </div>
        <div className="divide-y divide-slate-50">
          {issues.map((issue, idx) => (
            <div key={idx} className="p-4 hover:bg-slate-50 transition-colors">
              <div className="flex items-start gap-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 mt-1 bg-slate-100 px-2 py-0.5 rounded">
                  {issue.component}
                </span>
                <p className="text-slate-700 font-medium">{issue.description}</p>
              </div>
            </div>
          ))}
          {issues.length === 0 && (
            <div className="p-8 text-center text-slate-500">No critical issues found! 🎉</div>
          )}
        </div>
      </div>

      {/* Recommendations / Quick Wins */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
        <div className="p-4 border-b border-slate-100 bg-green-50 flex items-center gap-2">
          <CheckCircle className="text-green-600" size={20} />
          <h3 className="font-semibold text-green-900">Recommended Actions</h3>
        </div>
        <div className="divide-y divide-slate-50">
          {recommendations.map((rec, idx) => (
            <div key={idx} className="p-4 hover:bg-slate-50 transition-colors">
              <div className="flex justify-between items-start mb-1">
                <h4 className="font-semibold text-slate-900">{rec.action}</h4>
                {rec.priority === 'quick_win' && (
                  <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-1 rounded-full">
                    Quick Win
                  </span>
                )}
                {rec.priority === 'high' && (
                  <span className="text-xs font-bold text-orange-600 bg-orange-100 px-2 py-1 rounded-full">
                    High Impact
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-600 mb-2">{rec.details}</p>
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span>Impact: <span className="capitalize text-slate-600">{rec.impact}</span></span>
                <span>Effort: <span className="capitalize text-slate-600">{rec.effort}</span></span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
