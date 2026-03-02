export default function ErrorMessage({ error, onRetry }) {
  return (
    <div className="p-4 bg-red-50 border border-accent-red/20 rounded-card text-center">
      <p className="text-accent-red font-medium mb-1">Something went wrong</p>
      <p className="text-text-secondary text-sm mb-3">{error?.message || 'Please try again.'}</p>
      {onRetry && (
        <button onClick={onRetry} className="px-3 py-1.5 bg-primary text-white text-sm rounded-button">
          Retry
        </button>
      )}
    </div>
  )
}
