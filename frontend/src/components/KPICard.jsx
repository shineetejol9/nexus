import React from 'react'

export default function KPICard({ label, value, icon: Icon, accent = 'sage', suffix = '' }) {
  const accentClass = accent === 'volt' ? 'text-volt' : accent === 'toad' ? 'text-toad' : 'text-sage'
  const glow = accent === 'volt' ? 'shadow-voltGlow' : 'shadow-glow'
  return (
    <div className={`nx-card p-5 flex flex-col gap-3 hover:border-white/15 transition-colors ${glow}`}>
      <div className="flex items-center justify-between">
        <span className="text-[10px] tracking-[0.2em] uppercase text-muted">{label}</span>
        {Icon && <Icon className={`w-4 h-4 ${accentClass}`} />}
      </div>
      <span className={`font-disp text-3xl leading-none ${accentClass}`}>
        {value ?? '—'}{suffix}
      </span>
    </div>
  )
}
