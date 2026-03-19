
import React from 'react';
import { motion } from 'framer-motion';
import { Book, Code, Terminal, Database } from 'lucide-react';

export function Docs() {
    return (
        <div className="py-12 md:py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-[250px_1fr] gap-12">
                {/* Sidebar */}
                <div className="hidden md:block">
                    <nav className="sticky top-24 space-y-4">
                        <div>
                            <h3 className="font-semibold text-slate-900 mb-2">Getting Started</h3>
                            <ul className="space-y-2 text-sm text-slate-600">
                                <li className="text-brand-600 font-medium">Introduction</li>
                                <li className="hover:text-brand-600 cursor-pointer">Installation</li>
                                <li className="hover:text-brand-600 cursor-pointer">Quick Start</li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="font-semibold text-slate-900 mb-2">Core Concepts</h3>
                            <ul className="space-y-2 text-sm text-slate-600">
                                <li className="hover:text-brand-600 cursor-pointer">Score Calculation</li>
                                <li className="hover:text-brand-600 cursor-pointer">Grokopedia™</li>
                                <li className="hover:text-brand-600 cursor-pointer">Knowledge Graph</li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="font-semibold text-slate-900 mb-2">API Reference</h3>
                            <ul className="space-y-2 text-sm text-slate-600">
                                <li className="hover:text-brand-600 cursor-pointer">Endpoints</li>
                                <li className="hover:text-brand-600 cursor-pointer">Authentication</li>
                            </ul>
                        </div>
                    </nav>
                </div>

                {/* Main Content */}
                <div className="prose prose-slate max-w-none">
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        <h1>Documentation</h1>
                        <p className="lead">
                            Learn how to integrate the SEO Health Report into your workflow and master the art of Answer Engine Optimization (AEO).
                        </p>

                        <div className="bg-amber-50 border border-amber-200 rounded-lg p-6 my-8 not-prose">
                            <h3 className="text-amber-900 font-semibold flex items-center gap-2 mb-2">
                                <Terminal className="w-5 h-5" />
                                Quick Install
                            </h3>
                            <div className="bg-slate-900 text-slate-100 rounded p-4 font-mono text-sm overflow-x-auto">
                                npm install @raaptech/seo-health-report
                            </div>
                        </div>

                        <h2>What is "Grokopedia"?</h2>
                        <p>
                            "Grokopedia" is our term for the collective knowledge base that AIs (like xAI's Grok) use to generate answers. Unlike Wikipedia, which is static, Grokopedia is dynamic and real-time. Our tools help you influence this dynamic layer.
                        </p>

                        <div className="grid md:grid-cols-2 gap-6 my-8 not-prose">
                            <div className="border border-slate-200 rounded-xl p-6 hover:border-brand-300 transition-colors cursor-pointer">
                                <Code className="w-8 h-8 text-brand-500 mb-4" />
                                <h3 className="font-semibold text-slate-900 mb-2">API Reference</h3>
                                <p className="text-sm text-slate-600">Complete documentation for our REST API endpoints.</p>
                            </div>
                            <div className="border border-slate-200 rounded-xl p-6 hover:border-brand-300 transition-colors cursor-pointer">
                                <Database className="w-8 h-8 text-indigo-500 mb-4" />
                                <h3 className="font-semibold text-slate-900 mb-2">Data Models</h3>
                                <p className="text-sm text-slate-600">Understanding the schema of our audit reports.</p>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        </div>
    );
}
