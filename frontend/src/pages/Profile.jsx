import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'

export default function Profile() {
  const navigate = useNavigate()
  const { user, fetchUser, logout } = useAuth()

  const [name, setName] = useState(user?.name || '')
  const [flatNumber, setFlatNumber] = useState(user?.flat_number || '')
  const [isOwner, setIsOwner] = useState(user?.is_owner || false)
  const [bayNumber, setBayNumber] = useState(user?.bay_number || '')
  const [permission, setPermission] = useState(user?.availability_permission || 'anyone')
  const [credits, setCredits] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.users.credits().then((data) => setCredits(data.credits)).catch(() => {})
  }, [])

  // Reset form when user changes
  useEffect(() => {
    if (user) {
      setName(user.name)
      setFlatNumber(user.flat_number)
      setIsOwner(user.is_owner)
      setBayNumber(user.bay_number || '')
      setPermission(user.availability_permission || 'anyone')
    }
  }, [user])

  const handleSave = async (e) => {
    e.preventDefault()
    setError('')
    setSaved(false)
    setSaving(true)

    try {
      const updates = {
        name: name.trim(),
        flat_number: flatNumber.trim(),
        is_owner: isOwner,
        bay_number: isOwner ? bayNumber.trim() : null,
        availability_permission: isOwner ? permission : 'anyone',
      }
      await api.users.update(updates)
      await fetchUser()
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      setError(err.message || 'Failed to save changes.')
    } finally {
      setSaving(false)
    }
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  if (!user) return null

  return (
    <div className="max-w-content mx-auto page-enter">
      <h1 className="text-title-page font-bold text-text-primary mb-6">Profile</h1>

      {/* Credit balance */}
      <div className="bg-primary-light rounded-card p-4 mb-6 text-center">
        <p className="text-body text-text-secondary">Credit balance</p>
        <p className="text-hero font-bold text-primary">
          {credits !== null ? credits : user.credits}
        </p>
      </div>

      <form onSubmit={handleSave} className="bg-bg-card rounded-card shadow-sm border border-border p-5">
        <div className="space-y-4">
          {/* Phone (read-only) */}
          <div>
            <label className="block text-body font-medium text-text-primary mb-1">
              Phone number
            </label>
            <input
              type="tel"
              value={user.phone}
              readOnly
              className="w-full px-3 py-2.5 border border-border rounded-button text-body
                bg-bg-page text-text-secondary cursor-not-allowed"
            />
          </div>

          {/* Name */}
          <div>
            <label className="block text-body font-medium text-text-primary mb-1">
              Full name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2.5 border border-border rounded-button text-body
                focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
            />
          </div>

          {/* Flat number */}
          <div>
            <label className="block text-body font-medium text-text-primary mb-1">
              Flat number
            </label>
            <input
              type="text"
              value={flatNumber}
              onChange={(e) => setFlatNumber(e.target.value)}
              className="w-full px-3 py-2.5 border border-border rounded-button text-body
                focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
            />
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

          {isOwner && (
            <>
              <div>
                <label className="block text-body font-medium text-text-primary mb-1">
                  Bay number
                </label>
                <input
                  type="text"
                  value={bayNumber}
                  onChange={(e) => setBayNumber(e.target.value)}
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
        {saved && (
          <p className="text-accent-green text-body mt-3">Changes saved.</p>
        )}

        <button
          type="submit"
          disabled={saving}
          className="w-full mt-5 bg-primary text-white py-2.5 rounded-button font-medium
            hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </form>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full mt-4 border border-accent-red text-accent-red py-2.5 rounded-button
          font-medium hover:bg-red-50 transition-colors"
      >
        Log Out
      </button>
    </div>
  )
}
