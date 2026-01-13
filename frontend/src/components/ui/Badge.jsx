import React from 'react';
import { cn } from '../../lib/utils';

const badgeVariants = {
  default: "bg-slate-100 text-slate-800 border-slate-200",
  destructive: "bg-red-100 text-red-800 border-red-200",
  warning: "bg-yellow-100 text-yellow-800 border-yellow-200", 
  success: "bg-green-100 text-green-800 border-green-200",
  ai: "bg-ai-100 text-ai-800 border-ai-200"
};

const badgeSizes = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-2.5 py-1 text-sm"
};

export function Badge({ 
  className, 
  variant = "default", 
  size = "md",
  children, 
  ...props 
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border font-medium",
        badgeVariants[variant],
        badgeSizes[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}