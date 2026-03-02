import { useState, useEffect } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import TimelinePicker from '../components/TimelinePicker'
import CreditBadge from '../components/CreditBadge'
import Skeleton from '../components/Skeleton'
import Disclaimer from '../components/Disclaimer'

export default function BookingFlow() {
  const { bayId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { user, fetchUser } = useAuth()

  const initialDate = searchParams.get('date') || new Date().toISOString().split('T')[0]
  const initialStart = searchParams.get('start') ? parseInt(searchParams.get('start')) : null
  const initialEnd = searchParams.get('end') ? parseInt(searchParams.get('end')) : null

  const [bayInfo, setBayInfo] = useState(null)
  const [availableStart, setAvailableStart] = useState(0)
  const [availableEnd, setAvailableEnd] = useState(24)
  const [bookedRanges, setBookedRanges] = useState([])
  const [selectedStart, setSelectedStart] = useState(initialStart)
  const [selectedEnd, setSelectedEnd] = useState(initialEnd)
  const [date] = useState(initialDate)
  const [step, setStep] = useState(1) // 1=select, 2=confirm
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        // Load bay status for the date
        const start = initialStart || 0
        const end = initialEnd || 24
        const statusRes = await api.map.status(date, start, end)
        const bay = statusRes.bays?.find((b) => b.number === bayId)
        if (bay) {
          setBayInfo(bay)
          if (bay.available_start != null) setAvailableStart(bay.available_start)
          if (bay.available_end != null) setAvailableEnd(bay.available_end)
        }

        // Load existing bookings for this bay to find booked ranges
        // We use map status with full day range to detect
        const fullStatus = await api.map.status(date, 0, 24)
        const fullBay = fullStatus.bays?.find((b) => b.number === bayId)
        if (fullBay && fullBay.status === 'booked') {
          // The bay itself is fully booked for 0-24; we need finer granularity
          // For now mark as no booked ranges since we check per-hour
        }
        // Booked ranges would need a dedicated endpoint; for now we leave empty
        setBookedRanges([])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [bayId, date, initialStart, initialEnd])

  const creditCost = selectedStart != null && selectedEnd != null ? selectedEnd - selectedStart : 0
  const hasEnoughCredits = user && user.credits >= creditCost

  const handleTimeChange = (start, end) => {
    setSelectedStart(start)
    setSelectedEnd(end)
    setError(null)
  }

  const handleConfirm = () => {
    if (selectedStart == null || selectedEnd == null) return
    if (!hasEnoughCredits) {
      setError('Insufficient credits for this booking')
      return
    }
    setStep(2)
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    setError(null)
    try {
      await api.bookings.create({
        bay_number: bayId,
        date,
        start_hour: selectedStart,
        end_hour: selectedEnd,
      })
      await fetchUser() // Refresh credit balance
      navigate('/my-bookings')
    } catch (err) {
      setError(err.message)
      setStep(1)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton variant="title" />
        <Skeleton variant="card" count={2} />
        <Skeleton variant="text" count={3} />
      </div>
    )
  }

  return (
    <div className="space-y-6 page-enter">
      <h1 className="text-title-page font-bold">Book a Space</h1>

      {error && (
        <div className="bg-red-50 border border-accent-red text-accent-red rounded-card p-3 text-sm">
          {error}
        </div>
      )}

      <div className="bg-bg-card rounded-card p-4 border border-border">
        <div className="flex justify-between items-center mb-2">
          <div>
            <p className="font-semibold text-text-primary">Bay {bayId}</p>
            {bayInfo?.owner_name && (
              <p className="text-sm text-text-secondary">Owner: {bayInfo.owner_name}</p>
            )}
          </div>
          <div className="text-sm text-text-secondary">{date}</div>
        </div>
      </div>

      {/* Credit balance */}
      <div className="bg-bg-card rounded-card p-4 border border-border flex items-center justify-between">
        <span className="text-sm text-text-secondary">Your balance</span>
        <CreditBadge credits={user?.credits ?? 0} size="small" />
      </div>

      {step === 1 && (
        <>
          <div>
            <h2 className="text-title-section font-semibold mb-2">Select Hours</h2>
            <p className="text-sm text-text-secondary mb-3">
              Available: {availableStart}:00 - {availableEnd}:00
            </p>
            <TimelinePicker
              availableStart={availableStart}
              availableEnd={availableEnd}
              bookedRanges={bookedRanges}
              selectedStart={selectedStart}
              selectedEnd={selectedEnd}
              onChange={handleTimeChange}
            />
          </div>

          {creditCost > 0 && (
            <div className="text-sm text-text-secondary">
              Cost: <span className="font-semibold text-primary">{creditCost} {creditCost === 1 ? 'credit' : 'credits'}</span>
              {!hasEnoughCredits && (
                <span className="text-accent-red ml-2">(insufficient balance)</span>
              )}
            </div>
          )}

          <button
            type="button"
            className="w-full py-3 bg-primary text-white font-semibold rounded-button disabled:opacity-50"
            disabled={creditCost === 0 || !hasEnoughCredits}
            onClick={handleConfirm}
          >
            Continue
          </button>
        </>
      )}

      {step === 2 && (
        <>
          <div className="bg-bg-card rounded-card p-4 border border-border space-y-2">
            <h2 className="text-title-section font-semibold">Confirm Booking</h2>
            <div className="flex justify-between text-sm">
              <span className="text-text-secondary">Bay</span>
              <span className="font-medium">{bayId}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-text-secondary">Date</span>
              <span className="font-medium">{date}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-text-secondary">Time</span>
              <span className="font-medium">{selectedStart}:00 - {selectedEnd}:00</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-text-secondary">Cost</span>
              <span className="font-semibold text-primary">{creditCost} credits</span>
            </div>
          </div>

          <div className="px-2">
            <Disclaimer />
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              className="flex-1 py-3 border border-border text-text-primary font-semibold rounded-button"
              onClick={() => setStep(1)}
              disabled={submitting}
            >
              Back
            </button>
            <button
              type="button"
              className="flex-1 py-3 bg-primary text-white font-semibold rounded-button disabled:opacity-50"
              onClick={handleSubmit}
              disabled={submitting}
            >
              {submitting ? 'Booking...' : 'Confirm & Book'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
