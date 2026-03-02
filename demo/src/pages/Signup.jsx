import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import Disclaimer from '../components/Disclaimer'

export default function Signup() {
  const navigate = useNavigate()
  const location = useLocation()
  const { fetchUser } = useAuth()

  const email = location.state?.email

  const handleSkip = async () => {
    const demoEmail = 'jane@onespot.demo'
    await api.auth.requestOTP(demoEmail)
    await api.auth.verifyOTP(demoEmail, '000000')
    await fetchUser()
    navigate('/')
  }

  if (!email) {
    navigate('/login', { replace: true })
    return null
  }

  const [name, setName] = useState('')
  const [phone, setPhone] = useState('+44')
  const [isOwner, setIsOwner] = useState(false)
  const [floor, setFloor] = useState('')
  const [bayNumber, setBayNumber] = useState('')
  const [permission, setPermission] = useState('anyone')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!name.trim()) {
      setError('Please enter your name.')
      return
    }
    if (!phone.trim() || phone.length < 6) {
      setError('Please enter your phone number.')
      return
    }
    if (isOwner && !floor) {
      setError('Please select your floor.')
      return
    }
    if (isOwner && !bayNumber.trim()) {
      setError('Please enter your bay number.')
      return
    }

    setLoading(true)
    try {
      await api.users.register({
        name: name.trim(),
        phone: phone.trim(),
        email,
        is_owner: isOwner,
        bay_number: isOwner ? bayNumber.trim() : null,
        level: isOwner ? floor : null,
        availability_permission: isOwner ? permission : 'anyone',
      })
      await fetchUser()
      navigate('/')
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg-page flex items-center justify-center p-4">
      <div className="w-full max-w-content">
        <div className="bg-bg-card rounded-card shadow-sm border border-border p-6">
          <div className="text-center mb-6">
            <h1 className="text-title-page font-bold text-text-primary">Create Account</h1>
            <p className="text-body text-text-secondary mt-1">
              Set up your OneSpot profile
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              {/* Full name */}
              <div>
                <label className="block text-body font-medium text-text-primary mb-1">
                  Full name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Smith"
                  className="w-full px-3 py-2.5 border border-border rounded-button text-body
                    focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                  autoFocus
                />
              </div>

              {/* Email (read-only) */}
              <div>
                <label className="block text-body font-medium text-text-primary mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  readOnly
                  className="w-full px-3 py-2.5 border border-border rounded-button text-body
                    bg-bg-page text-text-secondary cursor-not-allowed"
                />
                <p className="text-xs text-text-secondary mt-1">For booking confirmations and reminders</p>
              </div>

              {/* Phone number (editable) */}
              <div>
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
                />
                <p className="text-xs text-text-secondary mt-1">So other residents can contact you about parking</p>
              </div>

              {/* Owner toggle */}
              <div className="flex items-center justify-between py-2">
                <label className="text-body font-medium text-text-primary">
                  I have a parking bay
                </label>
                <button
                  type="button"
                  role="switch"
                  aria-checked={isOwner}
                  onClick={() => setIsOwner(!isOwner)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                    ${isOwner ? 'bg-primary' : 'bg-gray-300'}`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                      ${isOwner ? 'translate-x-6' : 'translate-x-1'}`}
                  />
                </button>
              </div>

              {/* Owner-specific fields */}
              {isOwner && (
                <>
                  <div>
                    <label className="block text-body font-medium text-text-primary mb-2">
                      Floor
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => setFloor('G')}
                        className={`px-3 py-2.5 border rounded-button text-body font-medium transition-colors
                          ${floor === 'G'
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-border text-text-primary hover:border-gray-400'}`}
                      >
                        Ground level
                      </button>
                      <button
                        type="button"
                        onClick={() => setFloor('M')}
                        className={`px-3 py-2.5 border rounded-button text-body font-medium transition-colors
                          ${floor === 'M'
                            ? 'border-primary bg-primary/10 text-primary'
                            : 'border-border text-text-primary hover:border-gray-400'}`}
                      >
                        Mezzanine level
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-body font-medium text-text-primary mb-1">
                      Bay number
                    </label>
                    <input
                      type="text"
                      value={bayNumber}
                      onChange={(e) => setBayNumber(e.target.value)}
                      placeholder="e.g. 45"
                      className="w-full px-3 py-2.5 border border-border rounded-button text-body
                        focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                    />
                  </div>

                  <div>
                    <label className="block text-body font-medium text-text-primary mb-2">
                      Who can book your bay?
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="permission"
                          value="anyone"
                          checked={permission === 'anyone'}
                          onChange={(e) => setPermission(e.target.value)}
                          className="text-primary focus:ring-primary"
                        />
                        <span className="text-body text-text-primary">Anyone can book</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="permission"
                          value="owners_only"
                          checked={permission === 'owners_only'}
                          onChange={(e) => setPermission(e.target.value)}
                          className="text-primary focus:ring-primary"
                        />
                        <span className="text-body text-text-primary">Only other bay owners</span>
                      </label>
                    </div>
                  </div>
                </>
              )}
            </div>

            {error && (
              <p className="text-accent-red text-body mt-3">{error}</p>
            )}

            <div className="mt-4 mb-2">
              <Disclaimer />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 bg-primary text-white py-2.5 rounded-button font-medium
                hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>
        </div>

        <button
          type="button"
          onClick={handleSkip}
          className="w-full mt-4 bg-accent-green text-white py-2.5 rounded-button font-medium
            hover:opacity-90 transition-opacity"
        >
          Enter Demo →
        </button>

        <div className="mt-4 px-2">
          <Disclaimer />
        </div>
      </div>
    </div>
  )
}
