import { useState, useEffect, useCallback } from 'react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import BookingCard from '../components/BookingCard'
import CreditBadge from '../components/CreditBadge'

export default function MyBookings() {
  const { user, fetchUser } = useAuth()
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchBookings = useCallback(async () => {
    try {
      setLoading(true)
      const data = await api.bookings.mine()
      setBookings(data.bookings || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchBookings()
  }, [fetchBookings])

  const handleCancel = async (bookingId) => {
    try {
      await api.bookings.cancel(bookingId)
      await fetchBookings()
      await fetchUser() // Refresh credit balance
    } catch (err) {
      setError(err.message)
    }
  }

  const today = new Date().toISOString().split('T')[0]
  const upcoming = bookings.filter(
    (b) => b.date >= today && b.status === 'confirmed'
  )
  const past = bookings.filter(
    (b) => b.date < today || b.status === 'cancelled'
  )

  if (loading) {
    return (
      <div className="p-4 text-center text-text-secondary">Loading bookings...</div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-title-page font-bold">My Bookings</h1>
        <CreditBadge credits={user?.credits ?? 0} size="small" />
      </div>

      {error && (
        <div className="bg-red-50 border border-accent-red text-accent-red rounded-card p-3 text-sm">
          {error}
        </div>
      )}

      {bookings.length === 0 && (
        <div className="bg-bg-card rounded-card p-8 border border-border text-center">
          <p className="text-text-secondary">You have no bookings yet.</p>
          <p className="text-sm text-text-secondary mt-1">
            Browse available spaces on the map to make your first booking.
          </p>
        </div>
      )}

      {upcoming.length > 0 && (
        <div>
          <h2 className="text-title-section font-semibold mb-3">Upcoming</h2>
          <div className="space-y-3">
            {upcoming.map((booking) => (
              <BookingCard
                key={booking.id}
                booking={booking}
                onCancel={handleCancel}
              />
            ))}
          </div>
        </div>
      )}

      {past.length > 0 && (
        <div>
          <h2 className="text-title-section font-semibold mb-3">Past</h2>
          <div className="space-y-3">
            {past.map((booking) => (
              <BookingCard key={booking.id} booking={booking} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
