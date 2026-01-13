export const mockReport = {
  url: "https://example-corp.com",
  timestamp: new Date().toISOString(),
  overall_score: 72,
  grade: "C",
  component_scores: {
    technical: {
      score: 78,
      status: "fair",
      issues: [
        { severity: "critical", description: "LCP is 3.5s (Target < 2.5s)" },
        { severity: "high", description: "Missing Sitemap.xml" }
      ]
    },
    content: {
      score: 72,
      status: "fair",
      issues: [
        { severity: "medium", description: "3 pages with thin content (<500 words)" }
      ]
    },
    ai_visibility: {
      score: 65,
      grade: "D",
      components: {
        ai_presence: { score: 15, max: 25 },
        accuracy: { score: 16, max: 20 },
        parseability: { score: 12, max: 15 },
        knowledge_graph: { score: 8, max: 15 },
        citation_likelihood: { score: 10, max: 15 },
        sentiment: { score: 4, max: 10 }
      },
      ai_responses: [
        {
          system: "ChatGPT",
          found: false,
          query: "What is Example Corp?",
          response: "I don't have specific information about Example Corp in my training data."
        },
        {
          system: "Claude",
          found: true,
          query: "What is Example Corp?",
          response: "Example Corp appears to be a technology company, though I have limited information about their specific services and offerings."
        },
        {
          system: "Perplexity",
          found: true,
          query: "What is Example Corp?",
          response: "Example Corp is a mid-sized technology company founded in 2018, specializing in enterprise software solutions."
        }
      ],
      recommendations: [
        "Create Wikipedia entry to establish authority",
        "Optimize content for AI parsing with structured data",
        "Develop quotable, original research content"
      ],
      issues: [
        { severity: "high", description: "Brand not found in ChatGPT responses" },
        { severity: "medium", description: "No Wikipedia presence" }
      ]
    }
  },
  critical_issues: [
    { 
      component: "Technical", 
      description: "LCP is 3.5s (Target < 2.5s)",
      severity: "critical",
      details: "The Largest Contentful Paint metric indicates slow loading of main content. This affects user experience and Core Web Vitals scoring."
    },
    { 
      component: "AI Visibility", 
      description: "Brand not found in ChatGPT responses",
      severity: "high",
      details: "Your brand doesn't appear in ChatGPT responses for relevant queries, limiting AI-driven discovery."
    },
    { 
      component: "Technical", 
      description: "Missing Sitemap.xml",
      severity: "high",
      details: "No XML sitemap found. This makes it harder for search engines to discover and index your content efficiently."
    }
  ],
  recommendations: [
    {
      priority: "high",
      action: "Optimize Largest Contentful Paint (LCP)",
      details: "Compress hero images and defer non-critical JS.",
      impact: "high",
      effort: "medium"
    },
    {
      priority: "quick_win",
      action: "Submit Sitemap to GSC",
      details: "Generate xml sitemap and submit to Google Search Console.",
      impact: "high",
      effort: "low"
    },
    {
      priority: "medium",
      action: "Create Wikipedia Entry",
      details: "Establish notability through PR to qualify for Wikipedia.",
      impact: "high",
      effort: "high"
    }
  ]
};
