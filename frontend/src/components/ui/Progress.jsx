import { cn } from '../../lib/utils'

export function Progress({ className, value = 0, max = 100, ...props }) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)
  
  return (
    <div
      className={cn(
        'relative h-2 w-full overflow-hidden rounded-full bg-slate-100',
        className
      )}
      {...props}
    >
      <div
        className="h-full w-full flex-1 bg-brand-600 transition-all"
        style={{ transform: `translateX(-${100 - percentage}%)` }}
      />
    </div>
  )
}