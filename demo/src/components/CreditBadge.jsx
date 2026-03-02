export default function CreditBadge({ credits, size = 'default' }) {
  const sizeClasses = {
    hero: 'text-hero font-bold',
    default: 'text-title-page font-bold',
    small: 'text-emphasis font-semibold',
  }
  return (
    <div className="flex flex-col items-center">
      <span className={`${sizeClasses[size]} ${credits <= 0 ? 'text-accent-red' : 'text-primary'}`}>
        {credits}
      </span>
      <span className="text-xs text-text-secondary">{credits === 1 ? 'credit' : 'credits'}</span>
    </div>
  )
}
