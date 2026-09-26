import React from 'react'
import { Menu, LogOut, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { useNavigate } from 'react-router-dom'

export default function Header({ title, onMenu }) {
  const { user, role, signOut } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    signOut()
    navigate('/login')
  }

  return (
    <header className="h-16 shrink-0 border-b border-border bg-ink/80 backdrop-blur flex items-center justify-between px-4 lg:px-6 sticky top-0 z-30">
      <div className="flex items-center gap-3">
        <button className="lg:hidden text-muted" onClick={onMenu}><Menu className="w-5 h-5" /></button>
        <h1 className="font-disp text-xl tracking-wide uppercase">{title}</h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2 text-xs">
          <User className="w-4 h-4 text-volt" />
          <span className="text-paper/90">{user?.username || user?.email || 'User'}</span>
          {role && (
            <span className="nx-badge border border-sage/30 bg-sage/10 text-sage">{role}</span>
          )}
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-xs uppercase tracking-widest px-3 py-2 rounded-lg border border-border hover:border-toad/50 hover:text-toad transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" /> Logout
        </button>
      </div>
    </header>
  )
}
