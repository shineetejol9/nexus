import React, { useState } from 'react'
import Sidebar from './Sidebar.jsx'
import Header from './Header.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function AppLayout({ title, children }) {
  const { role } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="min-h-screen flex bg-ink">
      <Sidebar role={role} open={menuOpen} onClose={() => setMenuOpen(false)} />
      <div className="flex-1 min-w-0 flex flex-col">
        <Header title={title} onMenu={() => setMenuOpen(true)} />
        <main className="flex-1 p-4 lg:p-6 max-w-[1400px] w-full mx-auto">{children}</main>
      </div>
    </div>
  )
}
