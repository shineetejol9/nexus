import React from 'react'

// value expected 0-100 (or 0-1, auto-normalized)
export default function QualityCard({ label, value }) {
  const pct = value == null ? null : value <= 1 ? Math.round(value * 100) : Math.round(value)
  const color = pct == null ? 'bg-white/10' : pct >= 85 ? 'bg-sage' : pct >= 60 ? 'bg-volt' : 'bg-toad'
  return (
    <div className="nx-card p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] tracking-[0.15em] uppercase text-muted">{label}</span>
        <span className="text-sm font-bold text-paper">{pct == null ? '—' : `${pct}%`}</span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-white/5 overflow-hidden">
        <div className={`h-full ${color} transition-all duration-700`} style={{ width: `${pct ?? 0}%` }} />
      </div>
    </div>
  )
}
