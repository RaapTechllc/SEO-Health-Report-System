import { AIVisibilityPanel } from './AIVisibilityPanel'
import { PillarCard } from './PillarCard'
import { ActionCard } from './ActionCard'
import { mockReport } from '../../mockData'

export function DashboardShowcase() {
  const handleViewAnalysis = (pillar) => {
    console.log('View analysis for:', pillar)
  }

  const handleMarkComplete = (recommendation) => {
    console.log('Mark complete:', recommendation.action)
  }

  const handleLearnMore = (recommendation) => {
    console.log('Learn more:', recommendation.action)
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      <h1 className="text-3xl font-bold text-slate-900">SEO Health Dashboard</h1>
      
      {/* AI Visibility Showcase */}
      <section>
        <h2 className="text-xl font-semibold mb-4 text-ai-600">AI Visibility Analysis</h2>
        <AIVisibilityPanel data={mockReport.component_scores.ai_visibility} />
      </section>

      {/* Pillar Cards */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Performance Pillars</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {Object.entries(mockReport.component_scores).map(([pillar, data]) => (
            <PillarCard
              key={pillar}
              pillar={pillar}
              data={data}
              onViewAnalysis={handleViewAnalysis}
            />
          ))}
        </div>
      </section>

      {/* Action Cards */}
      <section>
        <h2 className="text-xl font-semibold mb-4">Recommended Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {mockReport.recommendations.map((recommendation, index) => (
            <ActionCard
              key={index}
              recommendation={recommendation}
              onMarkComplete={handleMarkComplete}
              onLearnMore={handleLearnMore}
            />
          ))}
        </div>
      </section>
    </div>
  )
}