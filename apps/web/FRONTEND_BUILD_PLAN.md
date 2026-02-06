# SEO Health Report Frontend - Build Plan

## Executive Summary

Transform the existing React + Vite + Tailwind foundation into a polished, user-friendly dashboard that showcases the AI Visibility differentiator while following 2026 design trends.

---

## 1. Typography & Font Strategy

### Recommended Font Stack

| Usage | Font | Why |
|-------|------|-----|
| Headings | **Inter** | Most popular UI font in 2025-2026, excellent readability, variable font support |
| Body | **Inter** | Consistent, clean, works at all sizes |
| Monospace (scores/data) | **JetBrains Mono** | Modern, readable for numbers and code |

### Implementation

```css
/* Google Fonts import - add to index.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
```

Inter is the go-to choice for dashboards—used by Linear, Vercel, and most modern SaaS products. It's optimized for screens and has excellent number legibility.

---

## 2. Component Library Strategy

### Recommendation: shadcn/ui Pattern

Why shadcn/ui approach over alternatives:
- Copy-paste model = full control, no dependency hell
- Built on Radix UI primitives = accessibility baked in
- Tailwind-native = matches existing setup
- AI-friendly = easy to customize

### Components to Build

| Component | Purpose |
|-----------|---------|
| `Card` | Pillar cards, issue cards |
| `Progress` | Score bars, loading states |
| `Tabs` | Report section navigation |
| `Dialog/Sheet` | Detailed drill-downs |
| `Tooltip` | Score explanations |
| `Badge` | Severity indicators |
| `Skeleton` | Loading states |
| `Accordion` | Expandable recommendations |

---

## 3. Data Visualization

### Library: Recharts

Why Recharts:
- React-native composable components
- SVG-based (crisp on all screens)
- Lightweight (~40kb gzipped)
- Perfect for dashboards

### Charts to Implement

| Chart Type | Use Case |
|------------|----------|
| **Radial Bar** | Overall score gauge (replace current SVG) |
| **Bar Chart** | Component score comparison |
| **Radar Chart** | Multi-dimensional audit breakdown |
| **Area Chart** | Historical score trends (future feature) |

---

## 4. Page Structure & User Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      LANDING PAGE                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Hero: "See How AI Sees Your Brand"                 │   │
│  │  URL Input + CTA Button                             │   │
│  │  Trust badges / sample report preview               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    LOADING STATE                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Animated progress with step indicators:            │   │
│  │  ✓ Crawling site → ✓ Analyzing content →           │   │
│  │  ⏳ Querying AI systems → Generating report         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    REPORT DASHBOARD                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  HEADER: Score + Grade + Quick Actions               │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  THREE PILLARS (Cards with drill-down)               │  │
│  │  [Technical 78] [Content 72] [AI Visibility 65]      │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  TABBED SECTIONS:                                    │  │
│  │  [Overview] [Technical] [Content] [AI] [Actions]     │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  ACTION PLAN: Prioritized recommendations            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Design System & Color Palette

### Updated Tailwind Config

```javascript
// tailwind.config.js
colors: {
  // Primary brand - Professional blue (trust, authority)
  brand: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
  },
  // Score colors (semantic)
  score: {
    excellent: '#10b981', // Green - A grade
    good: '#22c55e',      // Light green - B grade
    fair: '#f59e0b',      // Amber - C grade
    poor: '#f97316',      // Orange - D grade
    critical: '#ef4444',  // Red - F grade
  },
  // AI Visibility accent (differentiator)
  ai: {
    50: '#faf5ff',
    100: '#f3e8ff',
    500: '#a855f7',
    600: '#9333ea',
  }
}
```

### Visual Hierarchy

- Large score gauge as hero element
- AI Visibility pillar gets subtle purple accent to stand out
- Critical issues use red badges
- Quick wins use green "easy" badges

---

## 6. Component Specifications

### 6.1 Enhanced Score Gauge

```
┌─────────────────────┐
│    ╭───────────╮    │
│   ╱             ╲   │
│  │      72       │  │  ← Animated radial progress
│  │    Grade C    │  │
│   ╲             ╱   │
│    ╰───────────╯    │
│   "Needs Attention" │  ← Contextual message
└─────────────────────┘
```

### 6.2 Pillar Deep-Dive Cards

```
┌────────────────────────────────────┐
│ 🤖 AI Visibility          65/100  │
│ ─────────────────────────────────  │
│ ████████████░░░░░░░░  65%         │
│                                    │
│ ⚠️ Brand not found in ChatGPT     │
│ ⚠️ No Wikipedia presence          │
│                                    │
│ [View Full Analysis →]            │
└────────────────────────────────────┘
```

### 6.3 Action Plan Cards

```
┌────────────────────────────────────┐
│ 🎯 QUICK WIN                       │
│ ──────────────────────────────────│
│ Submit Sitemap to GSC              │
│                                    │
│ Impact: ████████░░ High            │
│ Effort: ██░░░░░░░░ Low             │
│                                    │
│ [Mark Complete] [Learn More]       │
└────────────────────────────────────┘
```

### 6.4 AI Visibility Showcase Section

This is the differentiator—make it visually distinct:

```
┌─────────────────────────────────────────────────────────┐
│  🤖 How AI Sees Your Brand                    [NEW]    │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │   ChatGPT   │ │   Claude    │ │  Perplexity │       │
│  │     ❌      │ │     ✓       │ │     ❌      │       │
│  │ Not Found   │ │  Mentioned  │ │  Not Found  │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                         │
│  Sample Response:                                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │ "When asked about [brand], Claude responded:    │   │
│  │  'I don't have specific information about...'"  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 7. Responsive Design Strategy

| Breakpoint | Layout |
|------------|--------|
| Mobile (<640px) | Single column, stacked cards, collapsible sections |
| Tablet (640-1024px) | 2-column pillar grid, side navigation |
| Desktop (>1024px) | 3-column pillar grid, full dashboard view |

---

## 8. Animations & Micro-interactions

### Key Animations

| Element | Animation |
|---------|-----------|
| Score gauge | Count-up animation on load (0 → actual score) |
| Progress bars | Smooth fill animation |
| Cards | Subtle hover lift (translateY + shadow) |
| Page transitions | Fade + slide-in |
| Loading states | Skeleton shimmer |

### Implementation Example

```javascript
// Use Framer Motion for smooth animations
import { motion } from 'framer-motion';

// Score count-up hook
const useAnimatedScore = (targetScore) => {
  const [displayScore, setDisplayScore] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => {
      setDisplayScore(prev => Math.min(prev + 1, targetScore));
    }, 20);
    return () => clearInterval(timer);
  }, [targetScore]);
  return displayScore;
};
```

---

## 9. Dependencies to Add

```bash
npm install recharts framer-motion @radix-ui/react-tabs @radix-ui/react-tooltip @radix-ui/react-progress @radix-ui/react-accordion
```

### Package Summary

| Package | Purpose |
|---------|---------|
| `recharts` | Charts and data visualization |
| `framer-motion` | Animations and transitions |
| `@radix-ui/react-tabs` | Accessible tab navigation |
| `@radix-ui/react-tooltip` | Hover tooltips |
| `@radix-ui/react-progress` | Progress bars |
| `@radix-ui/react-accordion` | Expandable sections |

---

## 10. File Structure

```
frontend/src/
├── components/
│   ├── ui/                    # Base UI components (shadcn-style)
│   │   ├── Button.jsx
│   │   ├── Card.jsx
│   │   ├── Badge.jsx
│   │   ├── Progress.jsx
│   │   ├── Tabs.jsx
│   │   ├── Tooltip.jsx
│   │   ├── Skeleton.jsx
│   │   └── Accordion.jsx
│   │
│   ├── dashboard/             # Dashboard-specific components
│   │   ├── ScoreGauge.jsx     # Enhanced radial gauge
│   │   ├── PillarCard.jsx     # Audit pillar cards
│   │   ├── ActionCard.jsx     # Recommendation cards
│   │   ├── IssuesList.jsx     # Critical issues
│   │   └── AIVisibilityPanel.jsx  # AI showcase section
│   │
│   ├── charts/                # Data visualization
│   │   ├── ScoreRadial.jsx    # Radial bar chart
│   │   ├── ComparisonBar.jsx  # Component comparison
│   │   └── TrendArea.jsx      # Historical trends
│   │
│   ├── layout/                # Layout components
│   │   ├── Header.jsx
│   │   ├── Footer.jsx
│   │   └── Container.jsx
│   │
│   └── forms/                 # Input components
│       └── AuditForm.jsx
│
├── hooks/                     # Custom React hooks
│   ├── useAnimatedScore.js
│   └── useAuditData.js
│
├── lib/                       # Utilities
│   ├── utils.js               # cn() helper, formatters
│   └── constants.js           # Grade mappings, colors
│
├── styles/
│   └── index.css              # Global styles + font imports
│
├── App.jsx
├── main.jsx
└── mockData.js
```

---

## 11. Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Update fonts (Inter + JetBrains Mono)
- [ ] Expand Tailwind color palette
- [ ] Create base UI components (Button, Card, Badge, Progress)
- [ ] Implement `cn()` utility for class merging

### Phase 2: Core Dashboard (Week 2)
- [ ] Enhanced ScoreGauge with Recharts radial bar
- [ ] Redesigned PillarCards with progress bars
- [ ] Tabbed navigation for report sections
- [ ] Skeleton loading states

### Phase 3: AI Visibility Showcase (Week 3)
- [ ] AIVisibilityPanel component
- [ ] AI system status cards (ChatGPT, Claude, Perplexity)
- [ ] Sample response display
- [ ] Purple accent theming

### Phase 4: Polish & Animations (Week 4)
- [ ] Framer Motion page transitions
- [ ] Score count-up animations
- [ ] Hover micro-interactions
- [ ] Mobile responsive refinements

### Phase 5: Backend Integration (Week 5+)
- [ ] Replace mock data with API calls
- [ ] Add error handling states
- [ ] Implement PDF export functionality
- [ ] Add historical report comparison

---

## 12. Key UX Principles

1. **Progressive Disclosure** - Show summary first, details on demand
2. **Visual Hierarchy** - Score gauge is the hero, everything else supports it
3. **Actionable Insights** - Every issue links to a recommendation
4. **AI Differentiation** - Purple accent makes AI Visibility stand out
5. **Mobile-First** - Works perfectly on phones for quick client demos

---

## 13. Utility Function: cn()

Create a class name merge utility for conditional styling:

```javascript
// lib/utils.js
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
```

---

## 14. Grade Mapping Constants

```javascript
// lib/constants.js
export const GRADE_CONFIG = {
  A: { min: 90, label: 'Excellent', color: 'score-excellent', message: 'Outstanding work!' },
  B: { min: 80, label: 'Good', color: 'score-good', message: 'Good, but room to grow.' },
  C: { min: 70, label: 'Needs Work', color: 'score-fair', message: 'Needs attention.' },
  D: { min: 60, label: 'Poor', color: 'score-poor', message: 'Significant improvements needed.' },
  F: { min: 0, label: 'Critical', color: 'score-critical', message: 'Critical issues detected.' },
};

export const getGradeFromScore = (score) => {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
};
```

---

## Quick Start

```bash
cd frontend
npm install recharts framer-motion @radix-ui/react-tabs @radix-ui/react-tooltip @radix-ui/react-progress @radix-ui/react-accordion
npm run dev
```
