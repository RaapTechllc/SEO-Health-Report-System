import React from 'react';
import ScoreGauge from './ScoreGauge';
import { ChevronRight } from 'lucide-react';

export default function PillarCard({ title, score, icon: Icon, description }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 flex flex-col items-center text-center hover:shadow-md transition-shadow cursor-pointer group">
      <div className="mb-4 p-3 bg-brand-50 rounded-full text-brand-600 group-hover:bg-brand-100 transition-colors">
        <Icon size={32} />
      </div>
      <h3 className="font-semibold text-lg text-slate-900 mb-1">{title}</h3>
      <p className="text-slate-500 text-sm mb-4">{description}</p>
      
      <div className="mt-auto">
        <ScoreGauge score={score} size="sm" />
      </div>
      
      <div className="mt-4 flex items-center text-sm font-medium text-brand-600 group-hover:text-brand-700">
        View Details <ChevronRight size={16} />
      </div>
    </div>
  );
}
