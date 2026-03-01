import { useState, useEffect, useMemo } from 'react'
import { useAuth } from '../context/AuthContext'
import { api } from '../api'
import WeekPatternEditor from '../components/WeekPatternEditor'
import Skeleton from '../components/Skeleton'

const DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

function getWeekDates(startDate) {
  // Returns 7 dates starting from the Monday of the week containing startDate
  const d = new Date(startDate)
  const dayOfWeek = d.getDay()
  const monday = new Date(d)
  monday.setDate(d.getDate() - ((dayOfWeek + 6) % 7))
  const dates = []
  for (let i = 0; i < 7; i++) {
    const date = new Date(monday)
    date.setDate(monday.getDate() + i)
    dates.push(date)
  }
  return dates
}

function formatDate(d) {
  return d.toISOString().split('T')[0]
}

function getThreeWeeksDates() {
  const today = new Date()
  const weeks = []
  for (let w = 0; w < 3; w++) {
    const weekStart = new Date(today)
    weekStart.setDate(today.getDate() + w * 7)
    weeks.push(getWeekDates(weekStart))
  }
  return weeks
}

function computeWeeklyHours(pattern) {
  if (!pattern) return 0
  let total = 0
  for (const day of DAY_NAMES) {
    const hours = pattern[day]
    if (hours && hours.start != null && hours.end != null) {
      total += hours.end - hours.start
    }
  }
  return total
}

function isDateAvailable(dateStr, availabilities) {
  const d = new Date(dateStr)
  const dayName = DAY_NAMES[((d.getDay() + 6) % 7)]

  for (const avail of availabilities) {
    if (avail.paused) continue

    if (avail.type === 'one_off' && avail.date === dateStr) {
      return true
    }

    if (avail.type === 'recurring') {
      if (avail.exclusions && avail.exclusions.includes(dateStr)) continue
      const dayHours = avail.pattern && avail.pattern[dayName]
      if (dayHours) return true
    }
  }
  return false
}

export default function MySpace() {
  const { user } = useAuth()
  const [availabilities, setAvailabilities] = useState([])
  const [pattern, setPattern] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  // One-off form
  const [oneOffDate, setOneOffDate] = useState('')
  const [oneOffStart, setOneOffStart] = useState(8)
  const [oneOffEnd, setOneOffEnd] = useState(18)
  const [addingOneOff, setAddingOneOff] = useState(false)

  const threeWeeks = useMemo(() => getThreeWeeksDates(), [])

  const fetchAvailability = async () => {
    try {
      const data = await api.availability.mine()
      setAvailabilities(data)
      // Extract recurring pattern
      const recurring = data.find((a) => a.type === 'recurring')
      if (recurring && recurring.pattern) {
        setPattern(recurring.pattern)
      }
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAvailability()
  }, [])

  const handleSavePattern = async () => {
    setError('')
    setSaved(false)
    setSaving(true)
    try {
      await api.availability.setRecurring({ pattern })
      await fetchAvailability()
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError(err.message || 'Failed to save pattern')
    } finally {
      setSaving(false)
    }
  }

  const handleAddOneOff = async () => {
    if (!oneOffDate) return
    setError('')
    setAddingOneOff(true)
    try {
      await api.availability.addOneOff({
        date: oneOffDate,
        start_hour: parseInt(oneOffStart, 10),
        end_hour: parseInt(oneOffEnd, 10),
      })
      setOneOffDate('')
      await fetchAvailability()
    } catch (err) {
      setError(err.message || 'Failed to add one-off window')
    } finally {
      setAddingOneOff(false)
    }
  }

  const handleDeleteOneOff = async (id) => {
    try {
      await api.availability.remove(id)
      await fetchAvailability()
    } catch (err) {
      setError(err.message || 'Failed to delete')
    }
  }

  const handleTogglePauseAll = async () => {
    try {
      for (const avail of availabilities) {
        await api.availability.togglePause(avail.id)
      }
      await fetchAvailability()
    } catch (err) {
      setError(err.message || 'Failed to toggle pause')
    }
  }

  if (!user || !user.is_owner) {
    return (
      <div className="max-w-content mx-auto">
        <h1 className="text-title-page font-bold text-text-primary">My Space</h1>
        <p className="text-text-secondary mt-2">You need to be a bay owner to manage availability.</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="max-w-content mx-auto">
        <Skeleton variant="title" className="mb-4" />
        <Skeleton variant="card" count={2} />
        <Skeleton variant="text" count={3} className="mt-4" />
      </div>
    )
  }

  const weeklyHours = computeWeeklyHours(pattern)
  const allPaused = availabilities.length > 0 && availabilities.every((a) => a.paused)
  const oneOffs = availabilities.filter((a) => a.type === 'one_off')

  return (
    <div className="max-w-content mx-auto page-enter">
      {/* Header */}
      <h1 className="text-title-page font-bold text-text-primary mb-1">
        My Space &mdash; Bay {user.bay_number}
      </h1>

      {/* Master toggle */}
      {availabilities.length > 0 && (
        <div className="flex items-center justify-between py-3 px-4 bg-bg-card rounded-card border border-border mb-4">
          <span className="text-body font-medium text-text-primary">Make my space unavailable</span>
          <button
            type="button"
            role="switch"
            aria-checked={allPaused}
            onClick={handleTogglePauseAll}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors
              ${allPaused ? 'bg-accent-red' : 'bg-gray-300'}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                ${allPaused ? 'translate-x-6' : 'translate-x-1'}`}
            />
          </button>
        </div>
      )}

      {/* Summary */}
      <div className="bg-primary-light rounded-card p-4 mb-6 text-center">
        <p className="text-body text-text-secondary">Your space is available</p>
        <p className="text-hero font-bold text-primary">{weeklyHours} hours</p>
        <p className="text-body text-text-secondary">this week</p>
      </div>

      {/* Recurring pattern editor */}
      <div className="mb-6">
        <h2 className="text-title-section font-semibold text-text-primary mb-3">Weekly Pattern</h2>
        <WeekPatternEditor pattern={pattern} onChange={setPattern} />

        {error && <p className="text-accent-red text-body mt-3">{error}</p>}
        {saved && <p className="text-accent-green text-body mt-3">Pattern saved.</p>}

        <button
          onClick={handleSavePattern}
          disabled={saving}
          className="w-full mt-4 bg-primary text-white py-2.5 rounded-button font-medium
            hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Pattern'}
        </button>
      </div>

      {/* One-off section */}
      <div className="mb-6">
        <h2 className="text-title-section font-semibold text-text-primary mb-3">One-off Availability</h2>

        <div className="bg-bg-card rounded-card border border-border p-4 space-y-3">
          <div>
            <label className="block text-body font-medium text-text-primary mb-1">Date</label>
            <input
              type="date"
              value={oneOffDate}
              onChange={(e) => setOneOffDate(e.target.value)}
              className="w-full px-3 py-2.5 border border-border rounded-button text-body
                focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-body font-medium text-text-primary mb-1">Start</label>
              <select
                value={oneOffStart}
                onChange={(e) => setOneOffStart(e.target.value)}
                className="w-full px-3 py-2.5 border border-border rounded-button text-body
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              >
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>
                    {String(i).padStart(2, '0')}:00
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-body font-medium text-text-primary mb-1">End</label>
              <select
                value={oneOffEnd}
                onChange={(e) => setOneOffEnd(e.target.value)}
                className="w-full px-3 py-2.5 border border-border rounded-button text-body
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              >
                {Array.from({ length: 24 }, (_, i) => i + 1).map((h) => (
                  <option key={h} value={h}>
                    {String(h).padStart(2, '0')}:00
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button
            onClick={handleAddOneOff}
            disabled={addingOneOff || !oneOffDate}
            className="w-full bg-accent-green text-white py-2.5 rounded-button font-medium
              hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {addingOneOff ? 'Adding...' : 'Add One-off Window'}
          </button>
        </div>

        {/* List of existing one-offs */}
        {oneOffs.length > 0 && (
          <div className="mt-3 space-y-2">
            {oneOffs.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between py-2 px-3 bg-bg-card rounded-button border border-border"
              >
                <span className="text-body text-text-primary">
                  {item.date} &middot; {String(item.start_hour).padStart(2, '0')}:00 &ndash;{' '}
                  {String(item.end_hour).padStart(2, '0')}:00
                  {item.paused && (
                    <span className="ml-2 text-accent-amber text-sm">(paused)</span>
                  )}
                </span>
                <button
                  onClick={() => handleDeleteOneOff(item.id)}
                  className="text-accent-red text-body hover:underline"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3-week calendar */}
      <div className="mb-6">
        <h2 className="text-title-section font-semibold text-text-primary mb-3">Next 3 Weeks</h2>
        <div className="space-y-3">
          {threeWeeks.map((week, wi) => (
            <div key={wi} className="grid grid-cols-7 gap-1">
              {week.map((day) => {
                const dateStr = formatDate(day)
                const available = isDateAvailable(dateStr, availabilities)
                const isToday = formatDate(new Date()) === dateStr
                return (
                  <div
                    key={dateStr}
                    className={`text-center py-2 rounded text-sm
                      ${available ? 'bg-primary-light text-primary font-medium' : 'bg-gray-100 text-text-secondary'}
                      ${isToday ? 'ring-2 ring-primary' : ''}`}
                  >
                    <div className="text-xs">
                      {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][day.getDay()]}
                    </div>
                    <div>{day.getDate()}</div>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
