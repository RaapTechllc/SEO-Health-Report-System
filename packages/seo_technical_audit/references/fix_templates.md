# Technical SEO Fix Templates

Standard recommendations for common technical SEO issues.

---

## Crawlability Fixes

### robots.txt Issues

**Entire site blocked (Disallow: /)**
```
Issue: All crawlers blocked from indexing site
Impact: Critical - Site will not appear in search results
Fix: Remove "Disallow: /" from robots.txt or specify only directories to block
Example:
  Before: Disallow: /
  After:  Disallow: /admin/
          Disallow: /private/
```

**Important resources blocked**
```
Issue: CSS/JS files blocked, preventing proper rendering
Impact: High - Pages may not be properly indexed
Fix: Allow CSS and JS files for all crawlers
Example:
  Add: Allow: /*.css
       Allow: /*.js
```

**Missing sitemap declaration**
```
Issue: Sitemap not declared in robots.txt
Impact: Low - Crawlers may not find sitemap
Fix: Add sitemap directive at end of robots.txt
Example:
  Sitemap: https://example.com/sitemap.xml
```

### Redirect Issues

**Long redirect chains**
```
Issue: Multiple redirects before reaching final URL
Impact: Medium - Wasted crawl budget, slower page loads
Fix: Update links to point directly to final destination
Example:
  Before: A -> B -> C -> D (3 hops)
  After:  A -> D (1 hop)
```

**302 instead of 301**
```
Issue: Temporary redirect used for permanent move
Impact: Low-Medium - SEO value may not pass fully
Fix: Change 302 to 301 in server configuration
Example (Apache):
  Before: Redirect 302 /old-page /new-page
  After:  Redirect 301 /old-page /new-page
```

**Redirect loop**
```
Issue: Page redirects create infinite loop
Impact: Critical - Page completely inaccessible
Fix: Audit redirect rules and remove circular references
```

### Canonical Issues

**Missing canonical tag**
```
Issue: No canonical URL specified
Impact: Medium - Potential duplicate content issues
Fix: Add self-referencing canonical to all pages
Example:
  <link rel="canonical" href="https://example.com/page" />
```

**Conflicting canonicals**
```
Issue: Canonical points to non-indexable page or different domain
Impact: High - Confusion about which page to index
Fix: Ensure canonical points to the correct, indexable version
```

---

## Speed Fixes

### LCP (Largest Contentful Paint)

**Large images**
```
Issue: Hero/above-fold images too large
Impact: High - Main content loads slowly
Fixes:
  1. Compress images (WebP format recommended)
  2. Use responsive images with srcset
  3. Implement lazy loading for below-fold images
  4. Preload hero image: <link rel="preload" as="image" href="hero.webp">
```

**Slow server response**
```
Issue: TTFB > 800ms
Impact: High - Everything delayed
Fixes:
  1. Upgrade hosting/server
  2. Implement caching (page cache, object cache)
  3. Use CDN
  4. Optimize database queries
  5. Enable compression (gzip/brotli)
```

**Render-blocking resources**
```
Issue: CSS/JS blocking initial render
Impact: Medium - Delayed content paint
Fixes:
  1. Inline critical CSS
  2. Defer non-critical JS: <script defer src="...">
  3. Async load non-essential scripts
  4. Remove unused CSS/JS
```

### CLS (Cumulative Layout Shift)

**Images without dimensions**
```
Issue: Images cause layout shift when loading
Impact: Medium - Poor user experience
Fix: Always specify width and height
Example:
  <img src="photo.jpg" width="800" height="600" alt="..." />
  Or use aspect-ratio in CSS
```

**Dynamic content injection**
```
Issue: Ads, embeds, or lazy content shifts layout
Impact: Medium - Frustrating for users
Fixes:
  1. Reserve space for dynamic content
  2. Use placeholder elements with fixed dimensions
  3. Avoid inserting content above existing content
```

**Web fonts causing shift**
```
Issue: Font swap causes text reflow
Impact: Low - Minor visual shift
Fix: Use font-display: optional or font-display: swap with fallback
```

### FID (First Input Delay)

**Long JavaScript tasks**
```
Issue: Main thread blocked by JS execution
Impact: High - Page unresponsive to user input
Fixes:
  1. Break up long tasks (>50ms)
  2. Use web workers for heavy computation
  3. Defer non-essential JavaScript
  4. Remove unused code
```

---

## Mobile Fixes

### Viewport Issues

**Missing viewport meta**
```
Issue: Page not configured for mobile
Impact: Critical - Page zoomed out on mobile
Fix: Add viewport meta tag
Example:
  <meta name="viewport" content="width=device-width, initial-scale=1">
```

**Content wider than viewport**
```
Issue: Horizontal scroll required
Impact: High - Poor mobile experience
Fixes:
  1. Use max-width: 100% on images
  2. Avoid fixed-width elements
  3. Use responsive CSS (flexbox, grid)
  4. Test at various viewport widths
```

### Touch Target Issues

**Small tap targets**
```
Issue: Buttons/links too small for fingers
Impact: Medium - Difficult to use on mobile
Fix: Minimum 48x48px tap targets with adequate spacing
Example CSS:
  .button {
    min-height: 48px;
    min-width: 48px;
    padding: 12px 16px;
  }
```

### Font Size Issues

**Text too small**
```
Issue: Text requires zooming to read
Impact: Medium - Accessibility concern
Fix: Use minimum 16px base font size
Example:
  body { font-size: 16px; }
  p { font-size: 1rem; } /* 16px */
```

---

## Security Fixes

### HTTPS Issues

**No HTTPS**
```
Issue: Site served over HTTP
Impact: Critical - "Not Secure" warning, no ranking benefit
Fixes:
  1. Obtain SSL certificate (Let's Encrypt is free)
  2. Install certificate on server
  3. Update internal links to HTTPS
  4. Set up HTTP -> HTTPS redirect
```

**Mixed content**
```
Issue: HTTP resources on HTTPS page
Impact: High - Security warnings, broken functionality
Fix: Update all resource URLs to HTTPS
Example:
  Before: <img src="http://example.com/image.jpg">
  After:  <img src="https://example.com/image.jpg">
  Or:     <img src="//example.com/image.jpg">
```

**HTTP doesn't redirect to HTTPS**
```
Issue: Both HTTP and HTTPS versions accessible
Impact: Medium - Duplicate content, less secure
Fix: Add server redirect
Example (Apache):
  RewriteEngine On
  RewriteCond %{HTTPS} off
  RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

### Security Headers

**Missing HSTS**
```
Issue: No HTTP Strict Transport Security
Impact: Medium - Vulnerable to downgrade attacks
Fix: Add HSTS header
Example:
  Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

**Missing X-Frame-Options**
```
Issue: Page can be embedded in iframes
Impact: Medium - Clickjacking vulnerability
Fix: Add X-Frame-Options header
Example:
  X-Frame-Options: DENY
  Or: X-Frame-Options: SAMEORIGIN
```

**Missing Content-Security-Policy**
```
Issue: No CSP defined
Impact: Medium - XSS vulnerability
Fix: Add basic CSP header (customize for your site)
Example:
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
```

---

## Structured Data Fixes

### Missing Schema

**No structured data**
```
Issue: No schema markup on page
Impact: Medium - Missing rich result opportunities
Fix: Add JSON-LD to <head>
Minimum for businesses:
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Company Name",
  "url": "https://example.com"
}
```

### Validation Errors

**Missing required properties**
```
Issue: Schema missing required fields
Impact: Medium - Won't qualify for rich results
Fix: Add missing properties per schema.org spec
```

**Invalid property values**
```
Issue: Property has wrong type/format
Impact: Medium - Schema may be ignored
Fix: Correct value format (dates, URLs, etc.)
Example:
  Before: "datePublished": "January 2024"
  After:  "datePublished": "2024-01-15"
```

### Rich Result Eligibility

**FAQ Schema**
```
Required: @type: "FAQPage", mainEntity array of Question/Answer
Template:
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "Question text?",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "Answer text."
    }
  }]
}
```

**Product Schema**
```
Required: name, image, description
Recommended: offers (with price, availability), aggregateRating
```

**Article Schema**
```
Required: headline, author, datePublished
Recommended: image, publisher, dateModified
```

---

## Quick Reference: Priority Matrix

| Issue | Impact | Effort | Priority |
|-------|--------|--------|----------|
| No HTTPS | Critical | Medium | 1 |
| Site blocked in robots.txt | Critical | Low | 1 |
| Poor LCP (>4s) | High | Medium | 2 |
| Missing sitemap | High | Low | 2 |
| Redirect loops | Critical | Low | 1 |
| Poor CLS (>0.25) | Medium | Low | 3 |
| Missing HSTS | Medium | Low | 3 |
| No structured data | Medium | Low | 3 |
| Missing canonical | Medium | Low | 3 |
| Small tap targets | Low | Medium | 4 |
