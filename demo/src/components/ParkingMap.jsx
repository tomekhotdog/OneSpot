import { useState, useMemo } from 'react'
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

  const { grid, cols } = useMemo(() => {
    const levelBays = bays.filter((b) => b.level === activeLevel)
    const maxRow = Math.max(...levelBays.map((b) => b.row), 0)
    const maxCol = Math.max(...levelBays.map((b) => b.col), 0)

    const lookup = new Map()
    for (const bay of levelBays) {
      lookup.set(`${bay.row}-${bay.col}`, bay)
    }

    const g = []
    for (let r = 0; r <= maxRow; r++) {
      for (let c = 0; c <= maxCol; c++) {
        g.push(lookup.get(`${r}-${c}`) || null)
      }
    }
    return { grid: g, cols: maxCol + 1 }
  }, [bays, activeLevel])

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
        <div
          className="inline-grid gap-[3px] p-3 bg-gray-50 rounded-xl w-full min-w-0"
          style={{ gridTemplateColumns: `repeat(${cols}, minmax(28px, 1fr))` }}
        >
          {grid.map((bay, i) =>
            bay ? (
              <BayCell key={bay.id} bay={bay} onSelect={onSelectBay} />
            ) : (
              <div key={`e${i}`} />
            )
          )}
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
