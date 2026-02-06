import React from 'react';
import { ScoreGauge } from './ScoreGauge';
import { PillarCard } from './PillarCard';
import { Layout, FileText, Bot } from 'lucide-react';

export function DashboardShowcase() {
  const pillars = [
    {
      title: "Technical SEO",
      score: 78,
      description: "Site speed, mobile friendliness, and crawlability metrics.",
      icon: Layout,
      color: "brand",
      issues: [
        { message: "Mobile viewport not configured", severity: "critical" },
        { message: "Slow First Contentful Paint", severity: "warning" },
        { message: "Missing sitemap.xml", severity: "info" }
      ]
    },
    {
      title: "Content Quality",
      score: 92,
      description: "Relevance, keyword optimization, and content depth.",
      icon: FileText,
      color: "brand",
      issues: [
        { message: "Low word count on homepage", severity: "warning" }
      ]
    },
    {
      title: "AI Visibility",
      score: 65,
      description: "How visible your brand is to AI search engines (ChatGPT, Claude).",
      icon: Bot,
      color: "ai",
      issues: [
        { message: "Brand not recognized by ChatGPT", severity: "critical" },
        { message: "No structured data for entities", severity: "warning" },
        { message: "Wikipedia presence missing", severity: "info" }
      ]
    }
  ];

  return (
    <div className="space-y-8 animate-in fade-in zoom-in duration-500">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Hero Gauge */}
        <div className="lg:col-span-1">
          <ScoreGauge score={78} grade="C" />
        </div>

        {/* Summary or Action Plan could go here */}
        <div className="lg:col-span-2 bg-white rounded-3xl p-8 border border-slate-100 shadow-sm flex flex-col justify-center">
          <h2 className="text-2xl font-bold mb-4">Executive Summary</h2>
          <p className="text-slate-600 mb-6 leading-relaxed">
            Your site has a solid foundation with excellent content quality, but technical issues are holding back your rankings.
            Critically, your <strong className="text-ai-600">AI Visibility</strong> is lagging behind competitors, meaning you may be invisible to the 100M+ users of ChatGPT and Perplexity.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-green-50 p-4 rounded-xl border border-green-100">
              <div className="text-sm text-green-600 font-semibold mb-1">Top Strength</div>
              <div className="font-medium text-slate-800">Content Quality (92/100)</div>
            </div>
            <div className="bg-red-50 p-4 rounded-xl border border-red-100">
              <div className="text-sm text-red-600 font-semibold mb-1">Top Weakness</div>
              <div className="font-medium text-slate-800">AI Visibility (65/100)</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {pillars.map((pillar, idx) => (
          <PillarCard key={idx} {...pillar} />
        ))}
      </div>
    </div>
  );
}