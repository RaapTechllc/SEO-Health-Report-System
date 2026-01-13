import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { Progress } from '../ui/Progress'
import { Button } from '../ui/Button'
import { getGradeFromScore } from '../../lib/constants'

const pillarIcons = {
  technical: '⚙️',
  content: '📝',
  ai_visibility: '🤖'
}

const pillarTitles = {
  technical: 'Technical SEO',
  content: 'Content & Authority',
  ai_visibility: 'AI Visibility'
}

export function PillarCard({ pillar, data, onViewAnalysis }) {
  const { score, issues = [] } = data
  const grade = getGradeFromScore(score)
  const isAI = pillar === 'ai_visibility'
  
  const topIssues = issues.slice(0, 3)

  return (
    <motion.div
      whileHover={{ y: -4, boxShadow: "0 10px 25px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)" }}
      transition={{ duration: 0.2 }}
    >
      <Card className={isAI ? 'border-ai-200 bg-ai-50/30' : ''}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <span className="text-lg">{pillarIcons[pillar]}</span>
              {pillarTitles[pillar]}
            </CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold">{score}</span>
              <span className="text-slate-500">/100</span>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress 
            value={score} 
            className={isAI ? 'bg-ai-100' : ''}
          />
          
          {topIssues.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-slate-700">Top Issues:</h4>
              <ul className="space-y-1">
                {topIssues.map((issue, index) => (
                  <li key={index} className="flex items-start gap-2 text-sm">
                    <span className="text-slate-400">•</span>
                    <span className="text-slate-600">{issue.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <Button 
            variant="outline" 
            size="sm" 
            className="w-full"
            onClick={() => onViewAnalysis?.(pillar)}
          >
            View Full Analysis
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  )
}