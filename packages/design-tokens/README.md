# RaapTech Design Tokens

Centralized design token system for consistent branding across all frontend apps.

## Files

| File | Purpose |
|------|---------|
| `colors.css` | Brand colors, semantic colors, grade colors, theme colors |
| `typography.css` | Font families and text sizes |
| `spacing.css` | Spacing scale, border radius, shadows |

## Integration

### Next.js (apps/web)

```tsx
// app/layout.tsx
import '@raaptech/design-tokens/colors.css';
import '@raaptech/design-tokens/typography.css';
import '@raaptech/design-tokens/spacing.css';
```

Or import all at once in your global CSS:

```css
/* globals.css */
@import '../../packages/design-tokens/colors.css';
@import '../../packages/design-tokens/typography.css';
@import '../../packages/design-tokens/spacing.css';
```

### React Dashboard (apps/dashboard)

```tsx
// src/main.tsx or src/index.tsx
import '../packages/design-tokens/colors.css';
import '../packages/design-tokens/typography.css';
import '../packages/design-tokens/spacing.css';
```

### Tailwind CSS Integration

Extend your `tailwind.config.js` to use these tokens:

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          primary: 'var(--color-brand-primary)',
          secondary: 'var(--color-brand-secondary)',
        },
        grade: {
          a: 'var(--color-grade-a)',
          b: 'var(--color-grade-b)',
          c: 'var(--color-grade-c)',
          d: 'var(--color-grade-d)',
          f: 'var(--color-grade-f)',
        },
      },
      fontFamily: {
        sans: 'var(--font-sans)',
        mono: 'var(--font-mono)',
      },
    },
  },
};
```

## Usage Examples

### CSS

```css
.header {
  background: var(--color-brand-gradient);
  color: var(--color-text-dark);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
}

.score-badge.grade-a {
  background-color: var(--color-grade-a);
}
```

### Tailwind (after config)

```html
<div class="bg-brand-primary text-white">
  <span class="text-grade-a">A+</span>
</div>
```

## Color Reference

### Brand Colors
- **Primary**: `#0ea5e9` (Sky-500) - Main brand blue
- **Secondary**: `#14b8a6` (Teal-500) - Secondary accent

### Score Grades
- **A (90-100)**: `#22c55e` Green
- **B (80-89)**: `#84cc16` Lime
- **C (70-79)**: `#f59e0b` Amber
- **D (60-69)**: `#f97316` Orange
- **F (0-59)**: `#ef4444` Red

### Themes
- **Dark Theme**: Default for dashboard apps
- **Light Theme**: Default for marketing/web apps
