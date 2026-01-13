import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'

const priorityConfig = {
  quick_win: { label: 'QUICK WIN', variant: 'excellent' },
  high: { label: 'HIGH', variant: 'poor' },
  medium: { label: 'MEDIUM', variant: 'fair' }
}

const impactLevels = {
  high: { width: '100%', color: 'bg-green-500' },
  medium: { width: '66%', color: 'bg-yellow-500' },
  low: { width: '33%', color: 'bg-red-500' }
}

const effortLevels = {
  low: { width: '33%', color: 'bg-green-500' },
  medium: { width: '66%', color: 'bg-yellow-500' },
  high: { width: '100%', color: 'bg-red-500' }
}

export function ActionCard({ recommendation, onMarkComplete, onLearnMore }) {
  const { priority, action, details, impact, effort } = recommendation
  const priorityStyle = priorityConfig[priority] || priorityConfig.medium

  return (
    <motion.div
      whileHover={{ y: -2, boxShadow: "0 4px 12px -2px rgba(0, 0, 0, 0.1)" }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant={priorityStyle.variant}>
                  {priorityStyle.label}
                </Badge>
              </div>
              <CardTitle className="text-base leading-tight">
                {action}
              </CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-slate-600">{details}</p>
          
          {/* Impact/Effort Bars */}
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-xs text-slate-600 mb-1">
                <span>Impact</span>
                <span className="capitalize">{impact}</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${impactLevels[impact]?.color || 'bg-gray-400'} transition-all`}
                  style={{ width: impactLevels[impact]?.width || '50%' }}
                />
              </div>
            </div>
            
            <div>
              <div className="flex justify-between text-xs text-slate-600 mb-1">
                <span>Effort</span>
                <span className="capitalize">{effort}</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div 
                  className={`h-full ${effortLevels[effort]?.color || 'bg-gray-400'} transition-all`}
                  style={{ width: effortLevels[effort]?.width || '50%' }}
                />
              </div>
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <Button 
              variant="outline" 
              size="sm" 
              className="flex-1"
              onClick={() => onMarkComplete?.(recommendation)}
            >
              Mark Complete
            </Button>
            <Button 
              variant="secondary" 
              size="sm" 
              className="flex-1"
              onClick={() => onLearnMore?.(recommendation)}
            >
              Learn More
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}