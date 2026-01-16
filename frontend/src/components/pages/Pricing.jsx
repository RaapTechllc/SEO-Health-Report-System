
import React from 'react';
import { motion } from 'framer-motion';
import { Check, Star, Shield, Zap } from 'lucide-react';

export function Pricing() {
    const tiers = [
        {
            name: "DIY Audit",
            price: "$199",
            period: "/month",
            onetime: "or $497 one-time",
            description: "Perfect for solopreneurs and small startups.",
            features: [
                "Automated AI Visibility Score",
                "Technical SEO Health Check",
                "Basic Content Citability Audit",
                "Standard PDF Export",
                "Weekly Email Alerts"
            ],
            cta: "Start Free Trial",
            popular: false,
        },
        {
            name: "Strategic Growth",
            price: "$1,500",
            period: "/month",
            onetime: "or $4,500 audit",
            description: "For agencies and growing brands.",
            features: [
                "Everything in DIY Audit",
                "Deep Competitor Benchmarking",
                "Strategic Action Plan (Phased)",
                "Grokopedia™ Optimization",
                "White-label Reports",
                "3 User Seats"
            ],
            cta: "Get Started",
            popular: true,
            highlight: "Most Popular",
        },
        {
            name: "Enterprise Partner",
            price: "$10,000",
            period: "/month",
            description: "Full service reputation & crisis management.",
            features: [
                "Everything in Strategic",
                "1-on-1 Strategy Consultation",
                "Human-Verified 'Persuasion' Audit",
                "Crisis Management Protocol",
                "Knowledge Graph Engineering",
                "Dedicated Account Manager",
                "24/7 Priority Support"
            ],
            cta: "Contact Sales",
            popular: false,
        },
    ];

    return (
        <div className="py-12 md:py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
                <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4">
                    Invest in Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-600 to-indigo-600">AI Reputation</span>
                </h2>
                <p className="text-xl text-slate-600 max-w-2xl mx-auto">
                    Choose the plan that fits your growth stage. Stop guessing how AI sees you.
                </p>
            </div>

            <div className="grid lg:grid-cols-3 gap-8 items-start">
                {tiers.map((tier, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className={`relative p-8 rounded-2xl border ${tier.popular
                                ? 'bg-white border-brand-200 shadow-xl ring-1 ring-brand-100 z-10 scale-105'
                                : 'bg-white border-slate-100 shadow-sm hover:shadow-md'
                            }`}
                    >
                        {tier.popular && (
                            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-brand-600 text-white px-4 py-1 rounded-full text-sm font-medium flex items-center gap-1">
                                <Star className="w-3 h-3fill-current" /> {tier.highlight}
                            </div>
                        )}

                        <h3 className="text-xl font-bold text-slate-900">{tier.name}</h3>
                        <p className="text-slate-500 mt-2 text-sm h-10">{tier.description}</p>

                        <div className="mt-6 mb-8">
                            <span className="text-4xl font-bold text-slate-900">{tier.price}</span>
                            <span className="text-slate-500">{tier.period}</span>
                            {tier.onetime && (
                                <div className="text-xs text-slate-400 mt-1 font-medium bg-slate-50 inline-block px-2 py-0.5 rounded">
                                    {tier.onetime}
                                </div>
                            )}
                        </div>

                        <button className={`w-full py-3 rounded-xl font-medium transition-all ${tier.popular
                                ? 'bg-brand-600 text-white hover:bg-brand-700 shadow-lg shadow-brand-200'
                                : 'bg-slate-50 text-slate-900 hover:bg-slate-100 border border-slate-200'
                            }`}>
                            {tier.cta}
                        </button>

                        <ul className="mt-8 space-y-4">
                            {tier.features.map((feature, i) => (
                                <li key={i} className="flex items-start gap-3 text-sm text-slate-600">
                                    <Check className={`w-5 h-5 flex-shrink-0 ${tier.popular ? 'text-brand-500' : 'text-slate-400'}`} />
                                    <span>{feature}</span>
                                </li>
                            ))}
                        </ul>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
