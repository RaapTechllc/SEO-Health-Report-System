# Accessibility Audit

Perform a comprehensive WCAG 2.1 AA accessibility audit of the page or component.

## Process

1. **Capture accessibility tree**
   - Use Playwright accessibility snapshot
   - Identify all interactive elements and their roles

2. **Semantic HTML check**
   - Verify proper heading hierarchy (h1 → h2 → h3, no skipping levels)
   - Ensure landmarks are used (header, nav, main, aside, footer)
   - Check that buttons are `<button>` elements, not divs
   - Verify links have meaningful text (not "click here")

3. **Image accessibility**
   - Check all `<img>` tags have descriptive alt text
   - Decorative images should have `alt=""` or `role="presentation"`
   - SVG icons need `aria-label` or accessible text

4. **Keyboard navigation**
   - Test tab order is logical
   - Verify all interactive elements are keyboard accessible
   - Check for visible focus indicators
   - Ensure no keyboard traps

5. **Color contrast**
   - Test all text against backgrounds (minimum 4.5:1 for normal text, 3:1 for large text)
   - Check interactive element states (hover, focus, disabled)
   - Verify color is not the only means of conveying information

6. **ARIA attributes**
   - Check for proper `aria-label`, `aria-labelledby`, `aria-describedby`
   - Verify `aria-expanded` on collapsible elements
   - Ensure `aria-hidden` is used correctly (not on focusable elements)
   - Check `role` attributes are appropriate

7. **Form accessibility**
   - All inputs have associated `<label>` elements
   - Error messages are announced to screen readers
   - Required fields are indicated accessibly (`aria-required` or required attribute)
   - Form validation is accessible

## Report Format

### WCAG 2.1 AA Violations

**Critical (Blocks usage):**
- Issue: Missing alt text on product images
- WCAG: 1.1.1 Non-text Content
- Fix: Add descriptive alt text: `<img src="product.jpg" alt="Blue cotton t-shirt, front view" />`

**Important (Creates barriers):**
- Issue: Insufficient color contrast on secondary buttons (2.8:1)
- WCAG: 1.4.3 Contrast (Minimum)
- Fix: Replace `bg-blue-300 text-blue-100` with `bg-blue-600 text-white`

**Recommended (Best practices):**
- Issue: Heading hierarchy skips from h1 to h3
- WCAG: 1.3.1 Info and Relationships
- Fix: Change `<h3>` to `<h2>` in section headers

### Summary

- Total issues: X
- Critical: X
- Important: X
- Recommended: X
