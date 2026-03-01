import { useState } from 'react'
import BayCell from './BayCell'

const legendItems = [
  { label: 'Available', color: 'bg-primary' },
  { label: 'Your Bay', color: 'bg-accent-green' },
  { label: 'Booked', color: 'bg-accent-amber' },
  { label: 'Unavailable', color: 'bg-gray-300' },
  { label: 'Restricted', color: 'bg-gray-200' },
]

export default function ParkingMap({ bays, levels, onSelectBay }) {
  const [activeLevel, setActiveLevel] = useState(levels?.[0]?.id || 'GF')

  const levelBays = bays.filter((b) => b.level === activeLevel)

  // Determine grid dimensions
  const maxRow = Math.max(...levelBays.map((b) => b.row), 0)
  const maxCol = Math.max(...levelBays.map((b) => b.col), 0)

  // Build grid
  const grid = []
  for (let r = 0; r <= maxRow; r++) {
    const row = []
    for (let c = 0; c <= maxCol; c++) {
      const bay = levelBays.find((b) => b.row === r && b.col === c)
      row.push(bay || null)
    }
    grid.push(row)
  }

  return (
    <div>
      {/* Level tabs */}
      <div className="flex gap-2 mb-4">
        {levels?.map((level) => (
          <button
            key={level.id}
            onClick={() => setActiveLevel(level.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeLevel === level.id
                ? 'bg-primary text-white'
                : 'bg-gray-100 text-text-secondary hover:bg-gray-200'
            }`}
          >
            {level.name}
          </button>
        ))}
      </div>

      {/* Bay grid */}
      <div className="overflow-x-auto">
        <div className="inline-flex flex-col gap-1.5 p-3 bg-gray-50 rounded-xl">
          {grid.map((row, ri) => (
            <div key={ri} className="flex gap-1.5">
              {row.map((bay, ci) =>
                bay ? (
                  <BayCell key={bay.id} bay={bay} onSelect={onSelectBay} />
                ) : (
                  <div key={`empty-${ri}-${ci}`} className="w-12 h-12" />
                )
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-4 text-xs text-text-secondary">
        {legendItems.map((item) => (
          <div key={item.label} className="flex items-center gap-1.5">
            <span className={`w-3 h-3 rounded ${item.color}`} />
            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
