import React, { useState, useEffect } from 'react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import { Activity } from 'lucide-react';

export function ScoreGauge({ score, grade, label = "Overall Health", className }) {
    const [animatedScore, setAnimatedScore] = useState(0);

    useEffect(() => {
        // Simple count-up animation
        const timeout = setTimeout(() => {
            setAnimatedScore(score);
        }, 500);
        return () => clearTimeout(timeout);
    }, [score]);

    const data = [
        {
            name: 'Score',
            value: animatedScore,
            fill: 'url(#scoreGradient)',
        },
    ];

    const getColor = (s) => {
        if (s >= 90) return '#10b981'; // brand-500
        if (s >= 80) return '#22c55e'; // green-500
        if (s >= 70) return '#f59e0b'; // amber-500
        if (s >= 60) return '#f97316'; // orange-500
        return '#ef4444'; // red-500
    };

    const color = getColor(score);

    return (
        <div className={cn("relative flex flex-col items-center justify-center p-6 bg-white rounded-3xl shadow-sm border border-slate-100", className)}>
            <div className="relative w-64 h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart
                        cx="50%"
                        cy="50%"
                        innerRadius="70%"
                        outerRadius="100%"
                        barSize={20}
                        data={data}
                        startAngle={180}
                        endAngle={0}
                    >
                        <defs>
                            <linearGradient id="scoreGradient" x1="0" y1="0" x2="1" y2="0">
                                <stop offset="0%" stopColor={color} stopOpacity={0.8} />
                                <stop offset="100%" stopColor={color} stopOpacity={1} />
                            </linearGradient>
                        </defs>
                        <PolarAngleAxis
                            type="number"
                            domain={[0, 100]}
                            angleAxisId={0}
                            tick={false}
                        />
                        <RadialBar
                            minAngle={15}
                            clockWise
                            background={{ fill: '#f1f5f9' }}
                            dataKey="value"
                            cornerRadius={10}
                        />
                    </RadialBarChart>
                </ResponsiveContainer>

                {/* Center Content */}
                <div className="absolute inset-0 flex flex-col items-center justify-center pt-12">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.2 }}
                        className="flex flex-col items-center"
                    >
                        <span className="text-6xl font-bold tracking-tighter text-slate-900">
                            {animatedScore}
                        </span>
                        <span className="text-sm font-medium text-slate-500 uppercase tracking-wider mt-1">
                            / 100
                        </span>
                        <div className={cn("mt-2 px-3 py-1 rounded-full text-xs font-bold uppercase",
                            grade === 'A' ? "bg-green-100 text-green-700" :
                                grade === 'B' ? "bg-green-100 text-green-700" :
                                    grade === 'C' ? "bg-amber-100 text-amber-700" :
                                        grade === 'D' ? "bg-orange-100 text-orange-700" :
                                            "bg-red-100 text-red-700"
                        )}>
                            Grade {grade}
                        </div>
                    </motion.div>
                </div>
            </div>

            <div className="mt-[-20px] text-center space-y-2">
                <h3 className="text-lg font-semibold text-slate-900">{label}</h3>
                <p className="text-sm text-slate-500 max-w-[200px]">
                    Based on 50+ weighted ranking factors
                </p>
            </div>

            <div className="absolute top-6 right-6">
                <div className="p-2 bg-slate-50 rounded-full text-slate-400">
                    <Activity size={20} />
                </div>
            </div>
        </div>
    );
}
