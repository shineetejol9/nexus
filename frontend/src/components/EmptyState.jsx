import React from 'react'
import { Inbox } from 'lucide-react'

export default function EmptyState({ title = 'Nothing here yet', hint }) {
  return (
    <div className="nx-card flex flex-col items-center justify-center text-center gap-3 py-16 px-6">
      <Inbox className="w-8 h-8 text-muted" />
      <p className="text-sm font-bold tracking-wide text-paper">{title}</p>
      {hint && <p className="text-xs text-muted max-w-sm">{hint}</p>}
    </div>
  )
}
