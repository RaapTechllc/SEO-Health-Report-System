import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { Badge } from '../ui/Badge'

export function AIVisibilityPanel({ data }) {
  const { ai_responses, score, grade } = data

  return (
    <Card className="border-l-4 border-l-ai-500">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-ai-600">
          🤖 How AI Sees Your Brand
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* AI System Status Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {ai_responses.map((response) => (
            <div
              key={response.system}
              className="p-4 rounded-lg border bg-ai-50"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">{response.system}</span>
                <Badge variant={response.found ? 'good' : 'poor'}>
                  {response.found ? 'Found' : 'Not Found'}
                </Badge>
              </div>
              <p className="text-sm text-slate-600">
                Query: "{response.query}"
              </p>
            </div>
          ))}
        </div>

        {/* Sample Response Display */}
        <div className="bg-ai-100 p-4 rounded-lg">
          <h4 className="font-medium mb-2 text-ai-600">Sample AI Response:</h4>
          {ai_responses.find(r => r.found) ? (
            <blockquote className="text-sm italic text-slate-700 border-l-2 border-ai-500 pl-3">
              "{ai_responses.find(r => r.found).response}"
            </blockquote>
          ) : (
            <p className="text-sm text-slate-500 italic">
              No positive responses found across AI systems.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}