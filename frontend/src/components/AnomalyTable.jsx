import React from 'react'
import { AlertTriangle } from 'lucide-react'

function formatRow(a) {
  if (a.row_index != null) return String(a.row_index)
  if (a.row == null) return '—'
  if (typeof a.row === 'object') return JSON.stringify(a.row)
  return String(a.row)
}

export default function AnomalyTable({ anomalies = [] }) {
  return (
    <div className="nx-card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-[0.15em] text-muted border-b border-border">
            <th className="px-5 py-3 font-normal">Column</th>
            <th className="px-5 py-3 font-normal">Value</th>
            <th className="px-5 py-3 font-normal">Lower Bound</th>
            <th className="px-5 py-3 font-normal">Upper Bound</th>
            <th className="px-5 py-3 font-normal">Row Data</th>
          </tr>
        </thead>
        <tbody>
          {anomalies.map((a, i) => (
            <tr key={a.id ?? i} className="border-b border-border/60 last:border-0 hover:bg-white/[0.03] transition-colors">
              <td className="px-5 py-3 font-bold text-paper flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-toad shrink-0" /> {a.column ?? a.column_name ?? '—'}
              </td>
              <td className="px-5 py-3 text-toad">{a.value != null ? String(a.value) : '—'}</td>
              <td className="px-5 py-3 text-muted">{a.lower_bound != null ? String(a.lower_bound) : '—'}</td>
              <td className="px-5 py-3 text-muted">{a.upper_bound != null ? String(a.upper_bound) : '—'}</td>
              <td className="px-5 py-3 text-muted font-mono text-xs max-w-xs truncate" title={formatRow(a)}>
                {formatRow(a)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
