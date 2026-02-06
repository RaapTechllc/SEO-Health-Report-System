import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react';
import { Card, CardHeader, CardContent, CardFooter } from '../ui/Card';
import { Progress } from '../ui/Progress';
import { Button } from '../ui/Button';
import { cn } from '../../lib/utils';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@radix-ui/react-tooltip';

export function PillarCard({ title, score, issues = [], icon: Icon, color = "brand", description }) {

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <XCircle className="text-red-500 w-4 h-4 mt-0.5 flex-shrink-0" />;
      case 'warning': return <AlertTriangle className="text-amber-500 w-4 h-4 mt-0.5 flex-shrink-0" />;
      default: return <Info className="text-blue-500 w-4 h-4 mt-0.5 flex-shrink-0" />;
    }
  };

  const getScoreColor = (s) => {
    if (s >= 90) return 'bg-green-500';
    if (s >= 80) return 'bg-green-500';
    if (s >= 70) return 'bg-amber-500';
    if (s >= 60) return 'bg-orange-500';
    return 'bg-red-500';
  };

  return (
    <Card className="h-full flex flex-col overflow-hidden border-t-4" style={{ borderTopColor: color === 'ai' ? '#a855f7' : '#3b82f6' }}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between mb-2">
          <div className={cn("p-2 rounded-lg", color === 'ai' ? "bg-ai-100 text-ai-600" : "bg-brand-100 text-brand-600")}>
            {Icon && <Icon size={20} />}
          </div>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold">{score}</span>
            <span className="text-sm text-slate-400">/100</span>
          </div>
        </div>
        <h3 className="font-semibold text-lg">{title}</h3>
        <p className="text-sm text-slate-500 line-clamp-2 min-h-[40px]">{description}</p>
      </CardHeader>

      <CardContent className="flex-grow space-y-6">
        {/* Score Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-medium text-slate-500">
            <span>Health Score</span>
            <span>{score}%</span>
          </div>
          <Progress value={score} className="h-2" indicatorColor={getScoreColor(score)} />
        </div>

        {/* Top Issues */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Top Priorities</h4>
          {issues.length > 0 ? (
            <div className="space-y-2">
              {issues.slice(0, 3).map((issue, idx) => (
                <div key={idx} className="flex gap-2 text-sm text-slate-600 group cursor-default">
                  {getSeverityIcon(issue.severity || 'warning')}
                  <span className="group-hover:text-slate-900 transition-colors">{issue.message || issue}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 p-3 rounded-md">
              <CheckCircle size={16} />
              <span>No critical issues found!</span>
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter className="pt-4 border-t border-slate-100 bg-slate-50/50">
        <Button variant="ghost" className="w-full justify-between group text-slate-600 hover:text-brand-600 hover:bg-transparent p-0">
          View Detailed Analysis
          <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
        </Button>
      </CardFooter>
    </Card>
  );
}