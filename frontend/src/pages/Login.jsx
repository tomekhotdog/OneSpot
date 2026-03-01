import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import Disclaimer from '../components/Disclaimer'

export default function Login() {
  const navigate = useNavigate()
  const { fetchUser } = useAuth()

  const [phone, setPhone] = useState('+44')
  const [step, setStep] = useState('phone') // 'phone' | 'code'
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [countdown, setCountdown] = useState(0)
  const codeInputRef = useRef(null)

  // Countdown timer
  useEffect(() => {
    if (countdown <= 0) return
    const timer = setInterval(() => {
      setCountdown((prev) => (prev <= 1 ? 0 : prev - 1))
    }, 1000)
    return () => clearInterval(timer)
  }, [countdown])

  // Focus code input when step changes
  useEffect(() => {
    if (step === 'code' && codeInputRef.current) {
      codeInputRef.current.focus()
    }
  }, [step])

  const formatCountdown = (seconds) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const handleSendCode = async (e) => {
    e.preventDefault()
    setError('')

    if (phone.length < 6) {
      setError('Please enter a valid phone number.')
      return
    }

    setLoading(true)
    try {
      const data = await api.auth.requestOTP(phone)
      setCountdown(data.expires_in || 300)
      setStep('code')
      setCode('')
    } catch (err) {
      if (err.status === 429) {
        setError('Too many requests. Please wait before trying again.')
      } else {
        setError(err.message || 'Failed to send code. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async (e) => {
    e.preventDefault()
    setError('')

    if (code.length !== 6) {
      setError('Please enter the 6-digit code.')
      return
    }

    setLoading(true)
    try {
      const data = await api.auth.verifyOTP(phone, code)
      if (data.is_new_user) {
        navigate('/signup', { state: { phone } })
      } else {
        await fetchUser()
        navigate('/')
      }
    } catch (err) {
      setError(err.message || 'Verification failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleResend = () => {
    setStep('phone')
    setCode('')
    setError('')
    setCountdown(0)
  }

  return (
    <div className="min-h-screen bg-bg-page flex items-center justify-center p-4">
      <div className="w-full max-w-content">
        <div className="bg-bg-card rounded-card shadow-sm border border-border p-6">
          <div className="text-center mb-6">
            <h1 className="text-title-page font-bold text-text-primary">OneSpot</h1>
            <p className="text-body text-text-secondary mt-1">
              Community parking sharing
            </p>
          </div>

          {step === 'phone' && (
            <form onSubmit={handleSendCode}>
              <label className="block text-body font-medium text-text-primary mb-1">
                Phone number
              </label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+447700900001"
                className="w-full px-3 py-2.5 border border-border rounded-button text-body
                  focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                autoFocus
              />

              {error && (
                <p className="text-accent-red text-body mt-2">{error}</p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-4 bg-primary text-white py-2.5 rounded-button font-medium
                  hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Sending...' : 'Send Code'}
              </button>
            </form>
          )}

          {step === 'code' && (
            <form onSubmit={handleVerify}>
              <p className="text-body text-text-secondary mb-3">
                We sent a 6-digit code to <span className="font-medium text-text-primary">{phone}</span>
              </p>

              <label className="block text-body font-medium text-text-primary mb-1">
                Verification code
              </label>
              <input
                ref={codeInputRef}
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                className="w-full px-3 py-2.5 border border-border rounded-button text-body text-center
                  tracking-widest text-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
              />

              {countdown > 0 && (
                <p className="text-body text-text-secondary mt-2 text-center">
                  Code expires in {formatCountdown(countdown)}
                </p>
              )}
              {countdown === 0 && step === 'code' && (
                <p className="text-body text-accent-red mt-2 text-center">
                  Code expired.
                </p>
              )}

              {error && (
                <p className="text-accent-red text-body mt-2">{error}</p>
              )}

              <button
                type="submit"
                disabled={loading || code.length !== 6}
                className="w-full mt-4 bg-primary text-white py-2.5 rounded-button font-medium
                  hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Verifying...' : 'Verify'}
              </button>

              <button
                type="button"
                onClick={handleResend}
                className="w-full mt-2 text-primary text-body font-medium py-2
                  hover:text-primary-dark transition-colors"
              >
                Use a different number
              </button>
            </form>
          )}
        </div>

        <div className="mt-4 px-2">
          <Disclaimer />
        </div>
      </div>
    </div>
  )
}
