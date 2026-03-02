import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import ParkingMap from '../components/ParkingMap'
import Skeleton from '../components/Skeleton'
import ErrorMessage from '../components/ErrorMessage'

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

const hours = Array.from({ length: 24 }, (_, i) => i)

export default function MapView() {
  const navigate = useNavigate()
  const [date, setDate] = useState(todayStr)
  const [start, setStart] = useState(8)
  const [end, setEnd] = useState(18)
  const [bays, setBays] = useState([])
  const [levels, setLevels] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Load bay layout once
  useEffect(() => {
    api.map.bays().then((data) => {
      setLevels(data.levels || [])
    })
  }, [])

  const fetchStatus = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.map.status(date, start, end)
      setBays(data.bays || [])
    } catch (err) {
      setError(err.message || 'Failed to load bay status')
    } finally {
      setLoading(false)
    }
  }, [date, start, end])

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  const handleSelectBay = (bay) => {
    navigate(`/book/${bay.number}?date=${date}&start=${start}&end=${end}`)
  }

  return (
    <div className="page-enter">
      <h1 className="text-title-page font-bold mb-4">Parking Map</h1>

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

      {/* Full-bleed map — breaks out of max-w-content */}
      <div className="w-[100vw] relative left-1/2 -translate-x-1/2 px-4 sm:px-6 lg:px-10">
        {error && (
          <ErrorMessage error={{ message: error }} onRetry={fetchStatus} />
        )}

        {loading ? (
          <Skeleton variant="card" count={3} className="mt-4" />
        ) : (
          <ParkingMap bays={bays} levels={levels} onSelectBay={handleSelectBay} />
        )}
      </div>
    </div>
  )
}
