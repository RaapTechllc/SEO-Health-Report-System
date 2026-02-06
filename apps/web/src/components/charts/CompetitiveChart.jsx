import React from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

export function CompetitiveChart({ data = [] }) {
  const defaultData = [
    { name: 'Your Site', score: 78, isYou: true },
    { name: 'Competitor A', score: 85, isYou: false },
    { name: 'Competitor B', score: 72, isYou: false },
    { name: 'Competitor C', score: 69, isYou: false },
    { name: 'Industry Avg', score: 65, isYou: false }
  ];

  const chartData = data.length > 0 ? data : defaultData;
  const yourScore = chartData.find(item => item.isYou)?.score || 0;
  const avgCompetitor = chartData.filter(item => !item.isYou && item.name !== 'Industry Avg')
    .reduce((sum, item) => sum + item.score, 0) / 3;

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-slate-700">Competitive Position</h3>
        <Badge variant={yourScore > avgCompetitor ? 'success' : 'warning'} size="sm">
          {yourScore > avgCompetitor ? 'Leading' : 'Behind'}
        </Badge>
      </div>
      
      <div className="h-32 mb-3">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
            <XAxis 
              dataKey="name" 
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: '#64748b' }}
            />
            <YAxis hide />
            <Bar dataKey="score" radius={[2, 2, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.isYou ? '#9333ea' : '#e2e8f0'} 
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      
      <div className="text-xs text-slate-600 space-y-1">
        <div className="flex justify-between">
          <span>Your Score:</span>
          <span className="font-medium text-ai-600">{yourScore}/100</span>
        </div>
        <div className="flex justify-between">
          <span>Avg Competitor:</span>
          <span className="font-medium">{Math.round(avgCompetitor)}/100</span>
        </div>
      </div>
    </Card>
  );
}