# Getting Into Knowledge Graphs

How to establish presence in the knowledge sources that feed AI systems.

---

## Why Knowledge Graphs Matter

Knowledge graphs are structured databases of facts. AI systems use them to:
- Verify information accuracy
- Answer factual questions
- Understand entity relationships
- Ground responses in verified data

**Key knowledge graphs:**
- **Wikipedia** - Most influential for AI training data
- **Google Knowledge Graph** - Powers Google's AI and search
- **Wikidata** - Structured data used by many AI systems
- **Industry databases** - Crunchbase, LinkedIn, etc.

---

## Wikipedia

### Notability Requirements

Wikipedia requires "notability" - significant coverage in reliable, independent sources.

**For companies, you need:**
- Coverage in major news outlets
- Industry publication features
- Award recognition
- Notable partnerships or clients
- Significant funding rounds (for startups)
- Regulatory filings (for public companies)

### Building Notability

1. **Press Coverage**
   - Pursue features in major publications
   - Respond to journalist queries (HARO, etc.)
   - Issue newsworthy press releases
   - Share industry insights with reporters

2. **Industry Recognition**
   - Apply for industry awards
   - Seek analyst coverage
   - Get featured in industry reports
   - Speak at conferences

3. **Public Milestones**
   - Announce significant achievements
   - Share growth metrics publicly
   - Highlight notable clients (with permission)
   - Document company history

### Wikipedia Article Creation

**DO NOT create your own Wikipedia article.** This violates Wikipedia's conflict of interest policy and will likely be deleted.

**Instead:**
- Ensure sufficient notability exists
- Make information easily findable for editors
- Wait for organic article creation
- If needed, request through Wikipedia's Articles for Creation

### If You Have an Article

- **Don't edit it directly** - conflict of interest
- Suggest corrections through Talk page
- Provide sources for disputed facts
- Report vandalism appropriately

### Creating a "Wikipedia-Ready" Website

Structure your website so Wikipedia editors can easily verify facts:

```
/about
  - Founded: [Date]
  - Founders: [Names]
  - Headquarters: [Location]
  - Key milestones with dates

/press
  - Links to press coverage
  - Press releases with dates
  - Award announcements

/team
  - Leadership bios
  - Professional backgrounds
```

---

## Google Knowledge Graph

### How to Appear

Google Knowledge Graph pulls from:
1. Wikipedia (most important)
2. Wikidata
3. Your website's structured data
4. Google Business Profile
5. Authoritative websites

### Structured Data Implementation

Add Organization schema to your homepage:

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Your Company Name",
  "alternateName": ["Alternate Name", "Abbreviation"],
  "url": "https://yourcompany.com",
  "logo": "https://yourcompany.com/logo.png",
  "image": "https://yourcompany.com/company-image.jpg",
  "description": "Official company description",
  "foundingDate": "2015-03-15",
  "founder": [
    {
      "@type": "Person",
      "name": "Jane Smith",
      "jobTitle": "CEO"
    }
  ],
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main Street",
    "addressLocality": "San Francisco",
    "addressRegion": "CA",
    "postalCode": "94102",
    "addressCountry": "US"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-555-123-4567",
    "contactType": "customer service",
    "availableLanguage": ["English"]
  },
  "sameAs": [
    "https://www.linkedin.com/company/yourcompany",
    "https://twitter.com/yourcompany",
    "https://www.facebook.com/yourcompany",
    "https://en.wikipedia.org/wiki/Your_Company"
  ],
  "numberOfEmployees": {
    "@type": "QuantitativeValue",
    "minValue": 50,
    "maxValue": 100
  }
}
```

### Google Business Profile

For local businesses especially:

1. Claim your Google Business Profile
2. Verify your business
3. Complete all information fields
4. Add photos and posts regularly
5. Respond to reviews
6. Keep hours and info current

### Consistency Across Web

Ensure consistent information on:
- Your website
- LinkedIn Company page
- Crunchbase profile
- Industry directories
- Social media profiles

Inconsistent data = lower confidence = less likely to appear in KG.

---

## Wikidata

### What is Wikidata

Wikidata is a free, collaborative database of structured data. Unlike Wikipedia (text), Wikidata stores facts as structured claims.

### Creating a Wikidata Item

1. **Check if you qualify**
   - Must have Wikipedia article, OR
   - Must have external identifier (ISNI, LEI, etc.), OR
   - Must be referenced in reliable sources

2. **Create the item**
   - Go to wikidata.org/wiki/Special:NewItem
   - Add label (company name) and description
   - Add statements (properties)

3. **Essential properties for organizations**
   - instance of (P31): business, company type
   - country (P17): headquarters country
   - headquarters location (P159): city
   - inception (P571): founding date
   - founder (P112): founder names
   - official website (P856): URL
   - social media links

### Example Wikidata Item Structure

```
Label: Acme Corporation
Description: American software company

Statements:
- instance of: software company
- country: United States
- headquarters location: San Francisco
- inception: 2015
- founder: Jane Smith
- official website: https://acme.com
- LinkedIn company ID: acme-corporation
- Twitter username: acme
```

### Maintaining Your Wikidata Item

- Update when facts change
- Add new properties as appropriate
- Link to Wikipedia article when created
- Add identifiers (LinkedIn, Twitter, etc.)

---

## Industry Databases

### Crunchbase

**For startups and tech companies:**
1. Claim your profile
2. Add all funding rounds
3. List founders and executives
4. Keep employee count current
5. Add news and milestones

### LinkedIn

**Company page optimization:**
1. Complete all company info
2. Add company description
3. List all locations
4. Post regular updates
5. Encourage employee profiles to link

### Industry-Specific

Depending on your industry:
- **Tech**: Crunchbase, AngelList, G2, Capterra
- **Finance**: Bloomberg, Reuters, SEC filings
- **Healthcare**: FDA databases, clinical trial registries
- **Legal**: Martindale-Hubbell, state bar associations
- **Real Estate**: MLS, property databases

---

## Verification and Monitoring

### Check Your Presence

1. **Google Knowledge Graph**
   - Search your brand name
   - Look for Knowledge Panel on right
   - Use Knowledge Graph API

2. **Wikipedia**
   - Search Wikipedia directly
   - Check if article exists
   - Review Talk page for discussions

3. **Wikidata**
   - Search wikidata.org
   - Check item completeness
   - Verify property accuracy

### Regular Audits

**Monthly:**
- Search brand name in Google
- Check Knowledge Panel accuracy
- Monitor Wikipedia for changes

**Quarterly:**
- Review all knowledge graph presence
- Update Wikidata properties
- Check industry database listings
- Ensure cross-platform consistency

### Handling Inaccuracies

| Platform | How to Correct |
|----------|----------------|
| Google KG | Use "Suggest an edit" on Knowledge Panel |
| Wikipedia | Discuss on Talk page, don't edit directly |
| Wikidata | Edit directly with sources |
| Crunchbase | Edit your claimed profile |
| LinkedIn | Edit your Company page |

---

## Timeline and Expectations

### Getting Into Knowledge Graphs

| Platform | Typical Timeline | Difficulty |
|----------|-----------------|------------|
| Wikidata | 1-2 weeks | Easy |
| Crunchbase | Immediate | Easy |
| LinkedIn | Immediate | Easy |
| Google KG | 1-6 months | Medium |
| Wikipedia | Months to years | Hard |

### Success Indicators

**Early wins:**
- Wikidata item created
- Crunchbase profile complete
- Google Business Profile verified
- Structured data validated

**Medium-term:**
- Google Knowledge Panel appears
- Brand searches show rich results
- AI systems return accurate info

**Long-term:**
- Wikipedia article exists
- Comprehensive Knowledge Graph presence
- AI systems cite you authoritatively

---

## Common Mistakes

1. **Creating your own Wikipedia article**
   - Violates conflict of interest policy
   - Will likely be deleted
   - Can harm your reputation

2. **Inconsistent information**
   - Different founding dates across platforms
   - Varying company descriptions
   - Conflicting employee counts

3. **Neglecting structured data**
   - No Organization schema
   - Missing or incorrect sameAs links
   - Outdated information

4. **Ignoring industry databases**
   - Unclaimed Crunchbase profile
   - Incomplete LinkedIn page
   - Missing from industry directories

5. **Not building notability**
   - No press coverage
   - No industry recognition
   - Nothing Wikipedia-worthy
