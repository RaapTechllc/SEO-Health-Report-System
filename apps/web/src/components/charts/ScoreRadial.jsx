import React from 'react';
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts';
import { getGradeFromScore, GRADE_CONFIG } from '../../lib/constants';

// Direct color mapping since Tailwind doesn't expose CSS variables by default
const SCORE_COLORS = {
  'score-excellent': '#10b981',
  'score-good': '#22c55e',
  'score-fair': '#f59e0b',
  'score-poor': '#f97316',
  'score-critical': '#ef4444',
};

export default function ScoreRadial({ score, size = 200 }) {
  const grade = getGradeFromScore(score);
  const gradeConfig = GRADE_CONFIG[grade];
  const fillColor = SCORE_COLORS[gradeConfig.color] || '#6b7280';
  
  const data = [
    {
      name: 'Score',
      value: score,
      fill: fillColor
    }
  ];

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart
          cx="50%"
          cy="50%"
          innerRadius="60%"
          outerRadius="90%"
          barSize={12}
          data={data}
          startAngle={90}
          endAngle={-270}
        >
          <RadialBar
            dataKey="value"
            cornerRadius={6}
            background={{ fill: '#f1f5f9' }}
          />
        </RadialBarChart>
      </ResponsiveContainer>
      
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-4xl font-bold" style={{ color: fillColor }}>
          {grade}
        </div>
        <div className="text-sm text-slate-600 mt-1">
          {score}/100
        </div>
      </div>
    </div>
  );
}