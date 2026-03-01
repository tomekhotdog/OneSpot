const statusStyles = {
  available: 'bg-primary text-white shadow-md cursor-pointer hover:bg-primary-dark',
  own: 'bg-accent-green text-white',
  unavailable: 'bg-gray-300 text-gray-500',
  booked: 'bg-accent-amber text-white',
  restricted: 'bg-gray-200 text-gray-400',
}

export default function BayCell({ bay, onSelect }) {
  const style = statusStyles[bay.status] || statusStyles.unavailable
  const label = bay.number.slice(-3)

  const handleClick = () => {
    if (bay.status === 'available' && onSelect) {
      onSelect(bay)
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={bay.status !== 'available'}
      className={`w-12 h-12 rounded-lg flex items-center justify-center text-xs font-semibold transition-colors ${style}`}
      title={`${bay.number} - ${bay.status}`}
    >
      {label}
    </button>
  )
}
