export default function DemoBanner() {
  const handleReset = () => {
    localStorage.removeItem('onespot_demo')
    sessionStorage.removeItem('onespot_demo_session')
    window.location.href = '/login'
  }

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-center text-sm text-amber-800">
      <span className="font-medium">Demo Mode</span> — data is stored locally in your browser. Any 6-digit code works for login.{' '}
      <button
        onClick={handleReset}
        className="underline font-medium hover:text-amber-900"
      >
        Reset data
      </button>
    </div>
  )
}
