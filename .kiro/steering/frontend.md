---
inclusion: fileMatch
fileMatchPattern: "frontend/**"
---

# Frontend Guidelines

React + Vite + Tailwind dashboard for SEO Health Report visualization.

## Tech Stack

- React 18 + Vite
- Tailwind CSS 3.4
- Recharts (data visualization)
- Framer Motion (animations)
- Lucide React (icons)

## Component Patterns

### UI Components (shadcn/ui style)

Located in `frontend/src/components/ui/`. Copy-paste pattern, no external UI library.

```jsx
import { cn } from '../../lib/utils'

export function Component({ className, ...props }) {
  return <div className={cn("base-classes", className)} {...props} />
}
```

### Dashboard Components

Located in `frontend/src/components/dashboard/`. Compose UI components for features.

### Charts

Located in `frontend/src/components/charts/`. Use Recharts.

## Color System

| Purpose | Tailwind Class | Usage |
|---------|---------------|-------|
| Brand | `brand-500/600/700` | Primary actions, headers |
| AI Accent | `ai-500/600` | AI Visibility section (differentiator) |
| Score Excellent | `score-excellent` | A grade (90+) |
| Score Good | `score-good` | B grade (80-89) |
| Score Fair | `score-fair` | C grade (70-79) |
| Score Poor | `score-poor` | D grade (60-69) |
| Score Critical | `score-critical` | F grade (<60) |

## Key Utilities

```javascript
// Class name merging
import { cn } from '../lib/utils'

// Grade helpers
import { GRADE_CONFIG, getGradeFromScore } from '../lib/constants'

// Animated score
import { useAnimatedScore } from '../hooks/useAnimatedScore'
```

## File Structure

```
frontend/src/
├── components/
│   ├── ui/           # Base components (Button, Card, Badge, etc.)
│   ├── dashboard/    # Feature components (PillarCard, AIVisibilityPanel)
│   └── charts/       # Recharts wrappers
├── hooks/            # Custom React hooks
├── lib/              # Utilities and constants
└── mockData.js       # Development mock data
```

## When Modifying

- Keep components minimal - single responsibility
- Use `cn()` for conditional class merging
- AI Visibility components get purple accent (`ai-*` colors)
- Score-related elements use semantic colors (`score-*`)
- Test build with `npm run build` before committing
