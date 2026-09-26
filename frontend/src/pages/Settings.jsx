import React from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, User, ShieldCheck, Clock } from 'lucide-react'
import AppLayout from '../components/AppLayout.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function Settings() {
  const { user, role, signOut } = useAuth()
  const navigate = useNavigate()

  return (
    <AppLayout title="Settings">
      <div className="max-w-lg nx-card p-6 space-y-5">
        <div className="flex items-center gap-3 pb-4 border-b border-border">
          <div className="w-11 h-11 rounded-full bg-sage/15 flex items-center justify-center">
            <User className="w-5 h-5 text-sage" />
          </div>
          <div>
            <p className="font-bold text-paper">{user?.username || '—'}</p>
            <p className="text-xs text-muted">{user?.email || 'No email on file'}</p>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-sm text-paper/90"><ShieldCheck className="w-4 h-4 text-volt" /> Role</span>
          <span className="nx-badge border border-sage/30 bg-sage/10 text-sage">{role || 'Unknown'}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-sm text-paper/90"><Clock className="w-4 h-4 text-volt" /> Session</span>
          <span className="text-xs text-muted">Authenticated via JWT</span>
        </div>

        <button
          onClick={() => { signOut(); navigate('/login') }}
          className="w-full flex items-center justify-center gap-2 text-xs uppercase tracking-widest px-4 py-3 rounded-lg
            border border-toad/30 text-toad hover:bg-toad/10 transition-colors mt-2"
        >
          <LogOut className="w-4 h-4" /> Log out
        </button>
      </div>
    </AppLayout>
  )
}
