import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import Skeleton from '../components/Skeleton'
import ErrorMessage from '../components/ErrorMessage'

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

const hours = Array.from({ length: 24 }, (_, i) => i)

export default function ListView() {
  const navigate = useNavigate()
  const [date, setDate] = useState(todayStr)
  const [start, setStart] = useState(8)
  const [end, setEnd] = useState(18)
  const [slots, setSlots] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchSlots = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.browse.available(date, start, end)
      setSlots(data.slots || [])
    } catch (err) {
      setError(err.message || 'Failed to load available spaces')
    } finally {
      setLoading(false)
    }
  }, [date, start, end])

  useEffect(() => {
    fetchSlots()
  }, [fetchSlots])

  const handleBook = (slot) => {
    navigate(`/book/${slot.bay_number}?date=${date}&start=${start}&end=${end}`)
  }

  return (
    <div className="page-enter">
      <h1 className="text-title-page font-bold mb-4">Browse Spaces</h1>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div>
          <label className="block text-xs text-text-secondary mb-1">Date</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="border border-border rounded-lg px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-xs text-text-secondary mb-1">From</label>
          <select
            value={start}
            onChange={(e) => setStart(Number(e.target.value))}
            className="border border-border rounded-lg px-3 py-2 text-sm"
          >
            {hours.map((h) => (
              <option key={h} value={h}>
                {String(h).padStart(2, '0')}:00
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-text-secondary mb-1">To</label>
          <select
            value={end}
            onChange={(e) => setEnd(Number(e.target.value))}
            className="border border-border rounded-lg px-3 py-2 text-sm"
          >
            {hours.map((h) => (
              <option key={h + 1} value={h + 1}>
                {String(h + 1).padStart(2, '0')}:00
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <ErrorMessage error={{ message: error }} onRetry={fetchSlots} />
      )}

      {loading ? (
        <Skeleton variant="card" count={3} className="mt-4" />
      ) : slots.length === 0 ? (
        <div className="text-center py-12 text-text-secondary">
          No spaces available for this time
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {slots.map((slot) => (
            <div
              key={slot.bay_number}
              className="bg-bg-card rounded-xl border border-border p-4 flex items-center justify-between"
            >
              <div>
                <div className="font-semibold text-text-primary">
                  Bay {slot.bay_number}
                  <span className="ml-2 text-xs text-text-secondary font-normal">
                    Level {slot.level}
                  </span>
                </div>
                <div className="text-sm text-text-secondary mt-1">
                  Available {String(slot.available_start).padStart(2, '0')}:00 -{' '}
                  {String(slot.available_end).padStart(2, '0')}:00
                </div>
              </div>
              <button
                onClick={() => handleBook(slot)}
                className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-dark transition-colors"
              >
                Book
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
