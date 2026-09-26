import React from 'react'
import { AlertTriangle, RotateCw } from 'lucide-react'

export default function ErrorMessage({ message = 'Something went wrong.', onRetry }) {
  return (
    <div className="nx-card border-toad/30 flex flex-col items-center justify-center text-center gap-3 py-14 px-6">
      <AlertTriangle className="w-8 h-8 text-toad" />
      <p className="text-sm text-paper max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-1 inline-flex items-center gap-2 text-xs uppercase tracking-widest px-4 py-2 rounded-lg border border-border hover:border-sage/50 hover:text-sage transition-colors"
        >
          <RotateCw className="w-3.5 h-3.5" /> Retry
        </button>
      )}
    </div>
  )
}
