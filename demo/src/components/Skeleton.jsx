export default function Skeleton({ variant = 'text', count = 1, className = '' }) {
  const base = 'animate-pulse bg-gray-200 rounded'
  const variants = {
    text: 'h-4 w-full',
    title: 'h-7 w-3/4',
    card: 'h-24 w-full rounded-card',
    circle: 'h-12 w-12 rounded-full',
    badge: 'h-16 w-20 rounded-card',
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className={`${base} ${variants[variant]}`} />
      ))}
    </div>
  )
}
