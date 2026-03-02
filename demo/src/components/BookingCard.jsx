import { useState } from 'react'

export default function BookingCard({ booking, onCancel }) {
  const [cancelling, setCancelling] = useState(false)

  const isConfirmed = booking.status === 'confirmed'
  const isFuture = booking.date >= new Date().toISOString().split('T')[0]
  const canCancel = isConfirmed && isFuture && onCancel

  const handleCancel = async () => {
    if (!onCancel) return
    setCancelling(true)
    try {
      await onCancel(booking.id)
    } finally {
      setCancelling(false)
    }
  }

  return (
    <div className="bg-bg-card rounded-card p-4 border border-border card-appear">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-primary-light text-primary text-sm font-bold rounded-button px-2 py-1">
            Mezzanine
          </div>
          <div>
            <p className="font-semibold text-text-primary">Bay {booking.bay_number}</p>
            <p className="text-sm text-text-secondary">{booking.date}</p>
            <p className="text-sm text-text-secondary">
              {booking.start_hour}:00 - {booking.end_hour}:00
            </p>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <span
            className={`text-xs font-semibold px-2 py-0.5 rounded-pill ${
              isConfirmed
                ? 'bg-accent-green-light text-accent-green'
                : 'bg-red-50 text-accent-red'
            }`}
          >
            {booking.status}
          </span>
          <span className="text-sm font-medium text-primary">
            {booking.credits_charged} {booking.credits_charged === 1 ? 'credit' : 'credits'}
          </span>
        </div>
      </div>

      {canCancel && (
        <button
          type="button"
          className="mt-3 w-full py-2 text-sm font-medium text-accent-red border border-accent-red rounded-button hover:bg-red-50 disabled:opacity-50"
          onClick={handleCancel}
          disabled={cancelling}
        >
          {cancelling ? 'Cancelling...' : 'Cancel Booking'}
        </button>
      )}
    </div>
  )
}
