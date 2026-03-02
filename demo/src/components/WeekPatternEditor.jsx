import { useCallback } from 'react'

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
const DAY_LABELS = {
  monday: 'Mon',
  tuesday: 'Tue',
  wednesday: 'Wed',
  thursday: 'Thu',
  friday: 'Fri',
  saturday: 'Sat',
  sunday: 'Sun',
}

const HOURS = Array.from({ length: 25 }, (_, i) => i) // 0-24

function formatHour(h) {
  if (h === 0) return '00:00'
  if (h === 24) return '24:00'
  return `${String(h).padStart(2, '0')}:00`
}

export default function WeekPatternEditor({ pattern = {}, onChange }) {
  const handleToggle = useCallback(
    (day) => {
      const current = pattern[day]
      const next = { ...pattern }
      if (current) {
        next[day] = null
      } else {
        next[day] = { start: 8, end: 18 }
      }
      onChange(next)
    },
    [pattern, onChange]
  )

  const handleChange = useCallback(
    (day, field, value) => {
      const next = { ...pattern }
      next[day] = { ...next[day], [field]: parseInt(value, 10) }
      onChange(next)
    },
    [pattern, onChange]
  )

  return (
    <div className="space-y-2">
      {DAYS.map((day) => {
        const hours = pattern[day]
        const isOn = hours != null

        return (
          <div
            key={day}
            className="flex items-center gap-3 py-2 px-3 bg-bg-card rounded-button border border-border"
          >
            {/* Day label */}
            <span className="w-10 text-body font-medium text-text-primary">{DAY_LABELS[day]}</span>

            {/* Toggle */}
            <button
              type="button"
              role="switch"
              aria-checked={isOn}
              onClick={() => handleToggle(day)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors shrink-0
                ${isOn ? 'bg-primary' : 'bg-gray-300'}`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${isOn ? 'translate-x-6' : 'translate-x-1'}`}
              />
            </button>

            {/* Hour selectors */}
            {isOn ? (
              <div className="flex items-center gap-2 text-body">
                <select
                  value={hours.start}
                  onChange={(e) => handleChange(day, 'start', e.target.value)}
                  className="px-2 py-1 border border-border rounded text-body focus:outline-none
                    focus:ring-1 focus:ring-primary"
                >
                  {HOURS.filter((h) => h < 24).map((h) => (
                    <option key={h} value={h}>
                      {formatHour(h)}
                    </option>
                  ))}
                </select>
                <span className="text-text-secondary">to</span>
                <select
                  value={hours.end}
                  onChange={(e) => handleChange(day, 'end', e.target.value)}
                  className="px-2 py-1 border border-border rounded text-body focus:outline-none
                    focus:ring-1 focus:ring-primary"
                >
                  {HOURS.filter((h) => h > 0).map((h) => (
                    <option key={h} value={h}>
                      {formatHour(h)}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <span className="text-body text-text-secondary">Unavailable</span>
            )}
          </div>
        )
      })}
    </div>
  )
}
