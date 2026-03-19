import React from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, Clock, Target, Zap } from 'lucide-react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { CompetitiveChart } from '../charts/CompetitiveChart';

export function ExecutiveBrief({ data = {} }) {
  const currentTime = new Date().toLocaleTimeString('en-US', { 
    hour: 'numeric', 
    minute: '2-digit',
    hour12: true 
  });

  const metrics = {
    organicTraffic: data.organicTraffic || { value: 12847, change: 8.2, trend: 'up' },
    revenue: data.revenue || { value: 45230, change: -2.1, trend: 'down' },
    keywordPositions: data.keywordPositions || { value: 156, change: 12, trend: 'up' },
    aiVisibility: data.aiVisibility || { score: 78, change: 5.3, trend: 'up' }
  };

  const alerts = data.alerts || [
    { type: 'competitor', message: 'Competitor launched new content strategy', priority: 'high' },
    { type: 'ai', message: 'AI search mentions increased 23%', priority: 'medium' },
    { type: 'technical', message: 'Core Web Vitals improved', priority: 'low' }
  ];

  return (
    <div className="max-w-md mx-auto bg-white min-h-screen">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 text-white p-4">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-lg font-semibold">Morning Brief</h1>
          <div className="flex items-center gap-1 text-slate-300">
            <Clock size={14} />
            <span className="text-sm">{currentTime}</span>
          </div>
        </div>
        <p className="text-slate-300 text-sm">SEO Performance Overview</p>
      </div>

      {/* Key Metrics Grid */}
      <div className="p-4 space-y-3">
        <MetricCard
          title="Organic Traffic"
          value={metrics.organicTraffic.value.toLocaleString()}
          change={metrics.organicTraffic.change}
          trend={metrics.organicTraffic.trend}
          icon={<Target size={16} />}
          color="blue"
        />
        
        <MetricCard
          title="Revenue Impact"
          value={`$${metrics.revenue.value.toLocaleString()}`}
          change={metrics.revenue.change}
          trend={metrics.revenue.trend}
          icon={<TrendingUp size={16} />}
          color="green"
        />
        
        <MetricCard
          title="Keyword Positions"
          value={metrics.keywordPositions.value}
          change={metrics.keywordPositions.change}
          trend={metrics.keywordPositions.trend}
          icon={<Target size={16} />}
          color="purple"
        />
        
        <MetricCard
          title="AI Visibility Score"
          value={metrics.aiVisibility.score}
          change={metrics.aiVisibility.change}
          trend={metrics.aiVisibility.trend}
          icon={<Zap size={16} />}
          color="ai"
          isScore={true}
        />
      </div>

      {/* Competitive Positioning */}
      <div className="px-4 pb-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">Competitive Position</h2>
        <CompetitiveChart data={data.competitive} />
      </div>

      {/* Competitive Alerts */}
      <div className="px-4 pb-4">
        <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
          <AlertTriangle size={14} />
          Priority Alerts
        </h2>
        <div className="space-y-2">
          {alerts.map((alert, index) => (
            <AlertCard key={index} alert={alert} />
          ))}
        </div>
      </div>

      {/* AI Search Changes */}
      <div className="px-4 pb-6">
        <h2 className="text-sm font-semibold text-slate-700 mb-3">AI Search Tracking</h2>
        <Card className="p-3 bg-ai-50 border-ai-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-ai-800">Brand Mentions</span>
            <Badge variant="ai" size="sm">+23%</Badge>
          </div>
          <div className="text-xs text-ai-600 space-y-1">
            <div>• ChatGPT: 8 new mentions</div>
            <div>• Claude: 5 new mentions</div>
            <div>• Perplexity: 3 new mentions</div>
          </div>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({ title, value, change, trend, icon, color, isScore = false }) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    green: 'bg-green-50 border-green-200 text-green-800',
    purple: 'bg-purple-50 border-purple-200 text-purple-800',
    ai: 'bg-ai-50 border-ai-200 text-ai-800'
  };

  const TrendIcon = trend === 'up' ? TrendingUp : TrendingDown;
  const trendColor = trend === 'up' ? 'text-green-600' : 'text-red-600';

  return (
    <Card className={`p-3 ${colorClasses[color]}`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-xs font-medium">{title}</span>
        </div>
        <div className={`flex items-center gap-1 text-xs ${trendColor}`}>
          <TrendIcon size={12} />
          <span>{Math.abs(change)}{isScore ? '' : '%'}</span>
        </div>
      </div>
      <div className="text-lg font-bold">
        {value}{isScore ? '/100' : ''}
      </div>
    </Card>
  );
}

function AlertCard({ alert }) {
  const priorityColors = {
    high: 'bg-red-50 border-red-200 text-red-800',
    medium: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    low: 'bg-green-50 border-green-200 text-green-800'
  };

  const priorityBadges = {
    high: 'destructive',
    medium: 'warning',
    low: 'success'
  };

  return (
    <Card className={`p-3 ${priorityColors[alert.priority]}`}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs flex-1">{alert.message}</p>
        <Badge variant={priorityBadges[alert.priority]} size="sm">
          {alert.priority}
        </Badge>
      </div>
    </Card>
  );
}