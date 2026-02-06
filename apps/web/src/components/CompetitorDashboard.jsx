import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { TrendingUp, TrendingDown, Minus, Trophy, Target, AlertTriangle } from 'lucide-react';

const CompetitorDashboard = ({ auditData, competitors = [] }) => {
  const [selectedMetric, setSelectedMetric] = useState('overall');
  const [viewMode, setViewMode] = useState('comparison');

  // Extract scores from audit data
  const yourScores = useMemo(() => ({
    name: auditData?.company_name || 'Your Site',
    technical: auditData?.audits?.technical?.score || 0,
    content: auditData?.audits?.content?.score || 0,
    ai_visibility: auditData?.audits?.ai_visibility?.score || 0,
    overall: auditData?.overall_score || 0,
  }), [auditData]);

  // Mock competitor data if not provided
  const competitorData = useMemo(() => {
    if (competitors.length > 0) return competitors;
    return [
      { name: 'Competitor A', technical: 78, content: 82, ai_visibility: 65, overall: 75 },
      { name: 'Competitor B', technical: 85, content: 70, ai_visibility: 72, overall: 76 },
      { name: 'Competitor C', technical: 72, content: 88, ai_visibility: 80, overall: 80 },
    ];
  }, [competitors]);

  // Combine data for charts
  const chartData = useMemo(() => [
    yourScores,
    ...competitorData
  ], [yourScores, competitorData]);

  // Radar chart data
  const radarData = useMemo(() => [
    { metric: 'Technical', ...chartData.reduce((acc, c) => ({ ...acc, [c.name]: c.technical }), {}) },
    { metric: 'Content', ...chartData.reduce((acc, c) => ({ ...acc, [c.name]: c.content }), {}) },
    { metric: 'AI Visibility', ...chartData.reduce((acc, c) => ({ ...acc, [c.name]: c.ai_visibility }), {}) },
  ], [chartData]);

  // Calculate rankings
  const rankings = useMemo(() => {
    const metrics = ['overall', 'technical', 'content', 'ai_visibility'];
    return metrics.reduce((acc, metric) => {
      const sorted = [...chartData].sort((a, b) => b[metric] - a[metric]);
      acc[metric] = sorted.findIndex(c => c.name === yourScores.name) + 1;
      return acc;
    }, {});
  }, [chartData, yourScores]);

  // Gap analysis
  const gaps = useMemo(() => {
    const leader = chartData.reduce((max, c) => 
      c.overall > max.overall ? c : max, chartData[0]);
    
    return {
      technical: leader.technical - yourScores.technical,
      content: leader.content - yourScores.content,
      ai_visibility: leader.ai_visibility - yourScores.ai_visibility,
      overall: leader.overall - yourScores.overall,
      leader: leader.name,
    };
  }, [chartData, yourScores]);

  const getTrendIcon = (gap) => {
    if (gap > 10) return <TrendingDown className="w-4 h-4 text-red-500" />;
    if (gap < -10) return <TrendingUp className="w-4 h-4 text-green-500" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 60) return 'text-orange-600';
    return 'text-red-600';
  };

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Competitor Analysis</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('comparison')}
            className={`px-4 py-2 rounded-lg ${viewMode === 'comparison' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
          >
            Comparison
          </button>
          <button
            onClick={() => setViewMode('radar')}
            className={`px-4 py-2 rounded-lg ${viewMode === 'radar' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
          >
            Radar
          </button>
        </div>
      </div>

      {/* Rankings Summary */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {['overall', 'technical', 'content', 'ai_visibility'].map((metric) => (
          <div key={metric} className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 capitalize">{metric.replace('_', ' ')}</span>
              {rankings[metric] === 1 && <Trophy className="w-4 h-4 text-yellow-500" />}
            </div>
            <div className="flex items-baseline gap-2 mt-1">
              <span className={`text-2xl font-bold ${getScoreColor(yourScores[metric])}`}>
                #{rankings[metric]}
              </span>
              <span className="text-sm text-gray-500">of {chartData.length}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Gap Analysis */}
      {gaps.overall > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <span className="font-semibold text-amber-800">Gap to Leader: {gaps.leader}</span>
          </div>
          <div className="grid grid-cols-4 gap-4 text-sm">
            {['technical', 'content', 'ai_visibility', 'overall'].map((metric) => (
              <div key={metric} className="flex items-center gap-2">
                {getTrendIcon(gaps[metric])}
                <span className="capitalize">{metric.replace('_', ' ')}:</span>
                <span className={gaps[metric] > 0 ? 'text-red-600' : 'text-green-600'}>
                  {gaps[metric] > 0 ? `-${gaps[metric]}` : `+${Math.abs(gaps[metric])}`} pts
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="h-80">
        {viewMode === 'comparison' ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Bar dataKey="technical" name="Technical" fill="#3b82f6" />
              <Bar dataKey="content" name="Content" fill="#10b981" />
              <Bar dataKey="ai_visibility" name="AI Visibility" fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" />
              <PolarRadiusAxis domain={[0, 100]} />
              {chartData.map((entry, idx) => (
                <Radar
                  key={entry.name}
                  name={entry.name}
                  dataKey={entry.name}
                  stroke={colors[idx % colors.length]}
                  fill={colors[idx % colors.length]}
                  fillOpacity={0.2}
                />
              ))}
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Detailed Comparison Table */}
      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 px-4">Competitor</th>
              <th className="text-center py-2 px-4">Overall</th>
              <th className="text-center py-2 px-4">Technical</th>
              <th className="text-center py-2 px-4">Content</th>
              <th className="text-center py-2 px-4">AI Visibility</th>
            </tr>
          </thead>
          <tbody>
            {chartData.map((competitor, idx) => (
              <tr 
                key={competitor.name} 
                className={`border-b ${idx === 0 ? 'bg-blue-50 font-semibold' : ''}`}
              >
                <td className="py-2 px-4 flex items-center gap-2">
                  {idx === 0 && <Target className="w-4 h-4 text-blue-600" />}
                  {competitor.name}
                </td>
                <td className={`text-center py-2 px-4 ${getScoreColor(competitor.overall)}`}>
                  {competitor.overall}
                </td>
                <td className={`text-center py-2 px-4 ${getScoreColor(competitor.technical)}`}>
                  {competitor.technical}
                </td>
                <td className={`text-center py-2 px-4 ${getScoreColor(competitor.content)}`}>
                  {competitor.content}
                </td>
                <td className={`text-center py-2 px-4 ${getScoreColor(competitor.ai_visibility)}`}>
                  {competitor.ai_visibility}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default CompetitorDashboard;
