# LLM Parseability Guide

How to structure your website so AI systems can easily extract and understand your content.

---

## Why Parseability Matters

AI systems need to:
1. **Crawl** - Access your content
2. **Parse** - Understand the structure
3. **Extract** - Pull out key information
4. **Synthesize** - Form accurate understanding

Poor structure = poor AI understanding = poor AI representation.

---

## Semantic HTML Essentials

### Page Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Page Title - Brand Name</title>
  <meta name="description" content="Clear, informative description">
</head>
<body>
  <header>
    <nav><!-- Navigation --></nav>
  </header>

  <main>
    <article>
      <header>
        <h1>Primary Page Title</h1>
        <p class="byline">By Author Name, Title</p>
        <time datetime="2024-01-15">January 15, 2024</time>
      </header>

      <section>
        <h2>Section Title</h2>
        <p>Content...</p>
      </section>

      <section>
        <h2>Another Section</h2>
        <p>More content...</p>
      </section>
    </article>

    <aside>
      <!-- Related content, sidebar -->
    </aside>
  </main>

  <footer>
    <!-- Footer content -->
  </footer>
</body>
</html>
```

### Element Usage Guide

| Element | Purpose | AI Benefit |
|---------|---------|------------|
| `<header>` | Page/section header | Identifies introductory content |
| `<nav>` | Navigation | Understands site structure |
| `<main>` | Primary content | Focuses on relevant content |
| `<article>` | Self-contained content | Identifies complete pieces |
| `<section>` | Thematic grouping | Understands content organization |
| `<aside>` | Tangential content | Knows what's supplementary |
| `<footer>` | Footer content | Identifies metadata, links |
| `<figure>` | Self-contained media | Associates captions with media |
| `<figcaption>` | Media caption | Provides context for images |
| `<time>` | Date/time | Understands temporal context |
| `<address>` | Contact info | Extracts contact details |

---

## Heading Hierarchy

### Correct Structure

```html
<h1>Complete Guide to Product Selection</h1>      <!-- One per page -->

<h2>Understanding Your Needs</h2>                  <!-- Major sections -->
  <h3>Budget Considerations</h3>                   <!-- Subsections -->
  <h3>Feature Requirements</h3>

<h2>Comparing Options</h2>
  <h3>Option A: Premium Choice</h3>
    <h4>Pros</h4>
    <h4>Cons</h4>
  <h3>Option B: Budget Choice</h3>
    <h4>Pros</h4>
    <h4>Cons</h4>

<h2>Making Your Decision</h2>
```

### Common Mistakes

```html
<!-- Bad: Multiple H1s -->
<h1>Company Name</h1>
<h1>Product Guide</h1>  <!-- Should be H2 -->

<!-- Bad: Skipping levels -->
<h1>Guide</h1>
<h4>Details</h4>  <!-- Should be H2 -->

<!-- Bad: Using headings for styling -->
<h3>This looks bold</h3>  <!-- Use CSS instead -->
```

---

## Content Structure Best Practices

### Paragraphs and Facts

```html
<!-- Good: Clear, factual paragraphs -->
<p>
  Acme Corp was founded in 2015 by Jane Smith in San Francisco.
  The company specializes in enterprise software solutions and
  serves over 500 customers worldwide.
</p>

<!-- Bad: Wall of text -->
<div>
  Acme Corp was founded in 2015 by Jane Smith in San Francisco the
  company specializes in enterprise software solutions and serves
  over 500 customers worldwide the company has grown significantly...
</div>
```

### Lists for Easy Extraction

```html
<!-- Good: Semantic list -->
<h2>Key Features</h2>
<ul>
  <li>Real-time analytics</li>
  <li>Custom dashboards</li>
  <li>API integration</li>
  <li>24/7 support</li>
</ul>

<!-- Bad: Comma-separated in paragraph -->
<p>Features: real-time analytics, custom dashboards, API integration, 24/7 support</p>
```

### Tables for Structured Data

```html
<!-- Good: Proper table with headers -->
<table>
  <caption>Pricing Plans</caption>
  <thead>
    <tr>
      <th>Plan</th>
      <th>Price</th>
      <th>Features</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Basic</td>
      <td>$29/month</td>
      <td>5 users, 10GB storage</td>
    </tr>
    <tr>
      <td>Pro</td>
      <td>$99/month</td>
      <td>25 users, 100GB storage</td>
    </tr>
  </tbody>
</table>
```

---

## Meta Information

### Essential Meta Tags

```html
<head>
  <!-- Page title: 50-60 characters -->
  <title>Product Name - Clear Description | Brand</title>

  <!-- Meta description: 150-160 characters -->
  <meta name="description" content="Clear, informative description
    that summarizes the page content accurately.">

  <!-- Canonical URL -->
  <link rel="canonical" href="https://example.com/page">

  <!-- Language -->
  <html lang="en">

  <!-- Open Graph for social/AI -->
  <meta property="og:title" content="Page Title">
  <meta property="og:description" content="Description">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://example.com/page">
</head>
```

### Author Attribution

```html
<!-- In article -->
<article>
  <header>
    <h1>Article Title</h1>
    <address class="author">
      By <a rel="author" href="/team/jane-smith">Jane Smith</a>,
      <span>Chief Product Officer</span>
    </address>
    <time datetime="2024-01-15" pubdate>January 15, 2024</time>
  </header>
</article>

<!-- Or with structured data -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "author": {
    "@type": "Person",
    "name": "Jane Smith",
    "jobTitle": "Chief Product Officer",
    "url": "https://example.com/team/jane-smith"
  }
}
</script>
```

---

## Images and Media

### Accessible Images

```html
<!-- Good: Descriptive alt text -->
<figure>
  <img src="dashboard.png"
       alt="Acme dashboard showing real-time analytics with
            sales graphs, user metrics, and conversion rates">
  <figcaption>The Acme dashboard provides real-time insights</figcaption>
</figure>

<!-- Bad: Missing or useless alt -->
<img src="dashboard.png" alt="image">
<img src="dashboard.png" alt="">
<img src="dashboard.png">  <!-- No alt at all -->
```

### Alt Text Guidelines

| Image Type | Alt Text Approach |
|------------|-------------------|
| Informational | Describe the content and purpose |
| Decorative | Empty alt (`alt=""`) |
| Functional | Describe the action/destination |
| Complex | Describe + link to detailed description |
| Text in image | Include all visible text |

---

## JavaScript Considerations

### Server-Side Rendering

AI crawlers may not execute JavaScript. Ensure critical content renders server-side.

```html
<!-- Good: Content in HTML -->
<main>
  <h1>Our Products</h1>
  <ul>
    <li>Product A</li>
    <li>Product B</li>
  </ul>
</main>

<!-- Bad: Content loaded via JS only -->
<main id="products">
  <!-- Products loaded dynamically -->
</main>
<script>
  loadProducts('#products');
</script>
```

### Testing Without JavaScript

1. Disable JavaScript in browser
2. View page source (not DevTools Elements)
3. Check if key content is visible
4. Use curl or wget to fetch raw HTML

### Noscript Fallback

```html
<noscript>
  <p>JavaScript is required for full functionality.
     However, you can still access our key information:</p>
  <ul>
    <li><a href="/about">About Us</a></li>
    <li><a href="/products">Products</a></li>
    <li><a href="/contact">Contact</a></li>
  </ul>
</noscript>
```

---

## Structured Data Implementation

### Organization (Required)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Acme Corporation",
  "url": "https://acme.com",
  "logo": "https://acme.com/logo.png",
  "description": "Enterprise software solutions",
  "foundingDate": "2015",
  "founder": {
    "@type": "Person",
    "name": "Jane Smith"
  },
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "San Francisco",
    "addressRegion": "CA",
    "postalCode": "94102",
    "addressCountry": "US"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-555-123-4567",
    "contactType": "customer service"
  },
  "sameAs": [
    "https://linkedin.com/company/acme",
    "https://twitter.com/acme"
  ]
}
```

### FAQ Page

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is Acme?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Acme is an enterprise software company..."
      }
    },
    {
      "@type": "Question",
      "name": "How much does Acme cost?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Acme plans start at $29/month..."
      }
    }
  ]
}
```

### Product

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Acme Pro",
  "description": "Enterprise analytics platform",
  "brand": {
    "@type": "Brand",
    "name": "Acme"
  },
  "offers": {
    "@type": "Offer",
    "price": "99.00",
    "priceCurrency": "USD",
    "priceValidUntil": "2024-12-31"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "150"
  }
}
```

---

## Common Issues and Fixes

### Issue: Heavy JavaScript Framework

**Symptoms:**
- Page source shows minimal content
- Content appears only after JS loads
- "View source" differs from rendered page

**Fixes:**
- Implement SSR (Server-Side Rendering)
- Use SSG (Static Site Generation)
- Add prerendering for important pages
- Ensure meta tags render server-side

### Issue: Div Soup

**Symptoms:**
- Many nested `<div>` elements
- No semantic elements
- Class names are only styling hints

**Fixes:**
- Replace `<div class="header">` with `<header>`
- Use `<main>`, `<article>`, `<section>`, `<aside>`
- Keep `<div>` for pure layout purposes

### Issue: Missing Alt Text

**Symptoms:**
- Images without alt attributes
- Alt text says "image" or filename
- Decorative images have verbose alt

**Fixes:**
- Add descriptive alt to informational images
- Use empty alt (`alt=""`) for decorative images
- Include key text that appears in images

### Issue: Poor Heading Structure

**Symptoms:**
- Multiple H1 tags
- Skipped heading levels
- Headings used for styling

**Fixes:**
- One H1 per page
- Sequential heading levels (H1 → H2 → H3)
- Use CSS for styling, semantic tags for structure

---

## Testing Tools

### Automated Testing
- Lighthouse (Chrome DevTools)
- WAVE Accessibility Tool
- axe DevTools
- HTML Validator (W3C)

### Manual Testing
- View page source (not DevTools)
- Disable JavaScript
- Use screen reader
- Check mobile rendering

### Schema Testing
- Google Rich Results Test
- Schema.org Validator
- Structured Data Linter
