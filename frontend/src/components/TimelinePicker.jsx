import { useState, useCallback } from 'react'

export default function TimelinePicker({
  availableStart,
  availableEnd,
  bookedRanges = [],
  selectedStart,
  selectedEnd,
  onChange,
}) {
  const [tapState, setTapState] = useState('idle') // idle | start_set | range_set

  const hours = []
  for (let h = availableStart; h < availableEnd; h++) {
    hours.push(h)
  }

  const isBooked = useCallback(
    (hour) => bookedRanges.some((r) => hour >= r.start && hour < r.end),
    [bookedRanges]
  )

  const isSelected = useCallback(
    (hour) =>
      selectedStart != null && selectedEnd != null && hour >= selectedStart && hour < selectedEnd,
    [selectedStart, selectedEnd]
  )

  const hasBookedInRange = (from, to) => {
    for (let h = from; h < to; h++) {
      if (isBooked(h)) return true
    }
    return false
  }

  const handleTap = (hour) => {
    if (isBooked(hour)) return

    if (tapState === 'idle' || tapState === 'range_set') {
      // First tap (or reset): set start hour
      onChange(hour, hour + 1)
      setTapState('start_set')
      return
    }

    if (tapState === 'start_set') {
      // Second tap: set end of range
      if (hour === selectedStart) {
        // Tapped same hour again — keep single hour selected
        setTapState('range_set')
        return
      }

      const rangeStart = Math.min(selectedStart, hour)
      const rangeEnd = Math.max(selectedStart, hour) + 1

      if (hasBookedInRange(rangeStart, rangeEnd)) {
        // Booked hours in the way — reset to this hour
        onChange(hour, hour + 1)
        setTapState('start_set')
        return
      }

      onChange(rangeStart, rangeEnd)
      setTapState('range_set')
    }
  }

  const isStart = (hour) => selectedStart != null && hour === selectedStart && tapState === 'start_set'

  return (
    <div className="space-y-2">
      <p className="text-xs text-text-secondary">
        {tapState === 'idle' && 'Tap a start hour'}
        {tapState === 'start_set' && 'Now tap an end hour'}
        {tapState === 'range_set' && 'Tap any hour to reselect'}
      </p>
      <div className="flex gap-1 overflow-x-auto pb-2">
        {hours.map((hour) => {
          const booked = isBooked(hour)
          const selected = isSelected(hour)
          const start = isStart(hour)

          let bgClass = 'bg-primary-light text-text-primary cursor-pointer hover:bg-primary hover:text-white'
          if (start) {
            bgClass = 'bg-primary text-white ring-2 ring-primary-dark cursor-pointer'
          } else if (selected) {
            bgClass = 'bg-primary text-white cursor-pointer'
          } else if (booked) {
            bgClass = 'bg-accent-amber text-white cursor-not-allowed'
          }

          return (
            <button
              key={hour}
              type="button"
              className={`flex-shrink-0 w-11 h-11 rounded-button text-sm font-medium flex items-center justify-center ${bgClass}`}
              onClick={() => handleTap(hour)}
              disabled={booked}
            >
              {hour}
            </button>
          )
        })}
      </div>
    </div>
  )
}
