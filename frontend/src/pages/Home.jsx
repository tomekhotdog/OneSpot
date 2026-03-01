import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api'
import CreditBadge from '../components/CreditBadge'
import BookingCard from '../components/BookingCard'

export default function Home() {
  const { user } = useAuth()
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadBookings() {
      try {
        const data = await api.bookings.mine()
        setBookings(data.bookings || [])
      } catch {
        // Silently fail — dashboard still usable
      } finally {
        setLoading(false)
      }
    }
    loadBookings()
  }, [])

  const today = new Date().toISOString().split('T')[0]
  const upcoming = bookings
    .filter((b) => b.date >= today && b.status === 'confirmed')
    .sort((a, b) => a.date.localeCompare(b.date) || a.start_hour - b.start_hour)
  const upcomingPreview = upcoming.slice(0, 3)
  const hasMore = upcoming.length > 3

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <h1 className="text-title-page font-bold">Hi, {user?.name || 'there'}!</h1>

      {/* Credit Balance Card */}
      <div className="bg-bg-card rounded-card p-6 border border-border flex justify-center">
        <CreditBadge credits={user?.credits ?? 0} size="hero" />
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3">
        <Link
          to="/map"
          className="flex-1 py-3 bg-primary text-white font-semibold rounded-button text-center text-sm"
        >
          Find a Space
        </Link>
        <Link
          to="/my-bookings"
          className="flex-1 py-3 border border-primary text-primary font-semibold rounded-button text-center text-sm"
        >
          My Bookings
        </Link>
      </div>

      {/* Owner Space Card */}
      {user?.is_owner && (
        <Link
          to="/my-space"
          className="block bg-bg-card rounded-card p-4 border border-border"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-text-primary">My Space</p>
              <p className="text-sm text-text-secondary">
                Bay {user.bay_number || '—'} — Manage availability
              </p>
            </div>
            <span className="text-text-secondary text-lg">&rarr;</span>
          </div>
        </Link>
      )}

      {/* Upcoming Bookings */}
      <div>
        <h2 className="text-title-section font-semibold mb-3">Upcoming Bookings</h2>
        {loading ? (
          <p className="text-sm text-text-secondary">Loading...</p>
        ) : upcomingPreview.length === 0 ? (
          <div className="bg-bg-card rounded-card p-6 border border-border text-center">
            <p className="text-text-secondary text-sm">
              No bookings yet — find a space on the{' '}
              <Link to="/map" className="text-primary font-medium underline">
                Map
              </Link>
              !
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {upcomingPreview.map((b) => (
              <BookingCard key={b.id} booking={b} />
            ))}
            {hasMore && (
              <Link
                to="/my-bookings"
                className="text-center text-sm text-primary font-medium py-2"
              >
                View all bookings
              </Link>
            )}
          </div>
        )}
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-text-secondary text-center px-4">
        OneSpot is a peer-to-peer parking sharing platform. Availability is provided by bay
        owners and is not guaranteed. Always confirm your booking before arriving.
      </p>
    </div>
  )
}
