import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Database, ShieldCheck, BarChart3, AlertTriangle,
  Workflow, UploadCloud, Users, Settings, X
} from 'lucide-react'

const NAV = [
  { to: '/dashboard', label: 'Overview', icon: LayoutDashboard, roles: null },
  { to: '/datasets', label: 'Datasets', icon: Database, roles: null },
  { to: '/quality', label: 'Quality', icon: ShieldCheck, roles: null },
  { to: '/analytics', label: 'Analytics', icon: BarChart3, roles: null },
  { to: '/anomalies', label: 'Anomalies', icon: AlertTriangle, roles: null },
  { to: '/pipelines', label: 'Pipelines', icon: Workflow, roles: null },
  { to: '/upload', label: 'Upload', icon: UploadCloud, roles: ['Admin', 'Data Engineer'] },
  { to: '/users', label: 'User Management', icon: Users, roles: ['Admin'] },
  { to: '/settings', label: 'Settings', icon: Settings, roles: null }
]

export default function Sidebar({ role, open, onClose }) {
  const items = NAV.filter((n) => !n.roles || (role && n.roles.includes(role)))

  return (
    <>
      {open && <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={onClose} />}
      <aside
        className={`fixed lg:static z-50 top-0 left-0 h-screen w-64 shrink-0 bg-panel border-r border-border
        flex flex-col transition-transform duration-300 ${open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        <div className="h-16 flex items-center justify-between px-5 border-b border-border">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-sage shadow-glow" />
            <span className="font-disp tracking-widest text-lg">NEXUS</span>
          </div>
          <button className="lg:hidden text-muted" onClick={onClose}><X className="w-5 h-5" /></button>
        </div>

        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {items.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-sage/10 text-sage border border-sage/25'
                    : 'text-paper/80 border border-transparent hover:bg-white/[0.04] hover:text-paper'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="tracking-wide">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-border text-[10px] tracking-[0.2em] uppercase text-muted">
          NODE // KONOHA.SYS
        </div>
      </aside>
    </>
  )
}
