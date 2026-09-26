import React from 'react'

function StatusBadge({ status }) {
  const s = (status || '').toUpperCase()
  const map = {
    SUCCESS: 'bg-sage/15 text-sage border-sage/30',
    RUNNING: 'bg-volt/15 text-volt border-volt/30',
    FAILED: 'bg-toad/15 text-toad border-toad/30'
  }
  return <span className={`nx-badge border ${map[s] || 'bg-white/10 text-muted border-white/10'}`}>{s || 'UNKNOWN'}</span>
}

export default function PipelineTable({ pipelines = [] }) {
  return (
    <div className="nx-card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-[0.15em] text-muted border-b border-border">
            <th className="px-5 py-3 font-normal">Pipeline ID</th>
            <th className="px-5 py-3 font-normal">Dataset ID</th>
            <th className="px-5 py-3 font-normal">Status</th>
            <th className="px-5 py-3 font-normal">Started</th>
            <th className="px-5 py-3 font-normal">Completed</th>
            <th className="px-5 py-3 font-normal text-right">Total</th>
            <th className="px-5 py-3 font-normal text-right">Clean</th>
            <th className="px-5 py-3 font-normal text-right">Bad</th>
          </tr>
        </thead>
        <tbody>
          {pipelines.map((p) => (
            <tr key={p.pipeline_id ?? p.id} className="border-b border-border/60 last:border-0 hover:bg-white/[0.03] transition-colors">
              <td className="px-5 py-3 font-bold text-paper">{p.pipeline_id ?? p.id}</td>
              <td className="px-5 py-3 text-muted">{p.dataset_id}</td>
              <td className="px-5 py-3"><StatusBadge status={p.status} /></td>
              <td className="px-5 py-3 text-muted">{p.started_at ? new Date(p.started_at).toLocaleString() : '—'}</td>
              <td className="px-5 py-3 text-muted">{p.completed_at ? new Date(p.completed_at).toLocaleString() : '—'}</td>
              <td className="px-5 py-3 text-right text-paper/90">{p.total_rows ?? '—'}</td>
              <td className="px-5 py-3 text-right text-sage">{p.clean_rows ?? '—'}</td>
              <td className="px-5 py-3 text-right text-toad">{p.bad_rows ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
