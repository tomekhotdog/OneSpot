import { useCallback } from 'react'

export default function TimelinePicker({
  availableStart,
  availableEnd,
  bookedRanges = [],
  selectedStart,
  selectedEnd,
  onChange,
}) {
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

  const handleTap = (hour) => {
    if (isBooked(hour)) return

    if (selectedStart == null) {
      // No selection yet: start here
      onChange(hour, hour + 1)
      return
    }

    // Try to extend the current selection to include this hour
    const newStart = Math.min(selectedStart, hour)
    const newEnd = Math.max(selectedEnd, hour + 1)

    // Check if the range from newStart to newEnd has any booked hours
    for (let h = newStart; h < newEnd; h++) {
      if (isBooked(h)) {
        // Non-contiguous due to booked block: reset
        onChange(hour, hour + 1)
        return
      }
    }

    onChange(newStart, newEnd)
  }

  return (
    <div className="flex gap-1 overflow-x-auto pb-2">
      {hours.map((hour) => {
        const booked = isBooked(hour)
        const selected = isSelected(hour)
        const unavailable = hour < availableStart || hour >= availableEnd

        let bgClass = 'bg-primary-light text-text-primary cursor-pointer hover:bg-primary hover:text-white'
        if (selected) {
          bgClass = 'bg-primary text-white cursor-pointer'
        } else if (booked) {
          bgClass = 'bg-accent-amber text-white cursor-not-allowed'
        } else if (unavailable) {
          bgClass = 'bg-gray-200 text-text-secondary cursor-not-allowed'
        }

        return (
          <button
            key={hour}
            type="button"
            className={`flex-shrink-0 w-11 h-11 rounded-button text-sm font-medium flex items-center justify-center ${bgClass}`}
            onClick={() => handleTap(hour)}
            disabled={booked || unavailable}
          >
            {hour}
          </button>
        )
      })}
    </div>
  )
}
