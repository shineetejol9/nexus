import React from 'react'

export default function Loading({ label = 'Loading…', full = false }) {
  return (
    <div className={full ? 'min-h-screen flex items-center justify-center bg-ink' : 'py-16 flex items-center justify-center'}>
      <div className="flex flex-col items-center gap-3">
        <div className="w-9 h-9 rounded-full border-2 border-sage/30 border-t-sage animate-spin" />
        <span className="text-[11px] tracking-[0.25em] uppercase text-muted">{label}</span>
      </div>
    </div>
  )
}
