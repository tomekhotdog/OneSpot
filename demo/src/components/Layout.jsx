import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Disclaimer from './Disclaimer'

const navItems = [
  { to: '/', label: 'Home', icon: '🏠' },
  { to: '/map', label: 'Map', icon: '🗺️' },
]

const ownerNav = { to: '/my-space', label: 'My Space', icon: '🅿️' }
const nonOwnerNav = { to: '/browse', label: 'Browse', icon: '🔍' }

export default function Layout() {
  const { user } = useAuth()

  const items = [
    ...navItems,
    user?.is_owner ? ownerNav : nonOwnerNav,
    { to: '/profile', label: 'Profile', icon: '👤' },
  ]

  return (
    <div className="min-h-screen bg-bg-page flex flex-col">
      <main className="flex-1 w-full max-w-content mx-auto px-4 pb-24 pt-4">
        <Outlet />
      </main>

      <footer className="w-full max-w-content mx-auto px-6 pb-20 text-center">
        <Disclaimer />
      </footer>

      <nav className="fixed bottom-0 inset-x-0 bg-bg-card border-t border-border">
        <div className="max-w-content mx-auto flex justify-around py-2">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 px-3 py-1 text-xs transition-colors ${
                  isActive ? 'text-primary font-semibold' : 'text-text-secondary'
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
