import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronRight, Download, Loader2, Database } from 'lucide-react'
import * as api from '../services/api.js'

// Reads fields defensively since exact backend field names may vary slightly.
export default function DatasetTable({ datasets = [] }) {
  const navigate = useNavigate()
  const [downloadingId, setDownloadingId] = useState(null)

  async function handleDownload(e, datasetId) {
    e.stopPropagation()
    if (!datasetId) return
    setDownloadingId(datasetId)
    try {
      await api.downloadDatasetFile(datasetId, 'clean')
    } catch (err) {
      console.error('Download failed:', err)
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <div className="nx-card overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-[0.15em] text-muted border-b border-border">
            <th className="px-5 py-3 font-normal">Dataset Name</th>
            <th className="px-5 py-3 font-normal">Latest Version</th>
            <th className="px-5 py-3 font-normal">Upload Date</th>
            <th className="px-5 py-3 font-normal">Database ID</th>
            <th className="px-5 py-3 font-normal text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {datasets.map((d) => {
            const id = d.dataset_id ?? d.id
            const fileName = d.file_name ?? d.filename ?? '—'
            const version = d.version ?? '—'
            const uploaded = d.upload_date ?? d.uploaded_at ?? d.created_at
            const totalVersions = d.totalVersions ?? 1

            return (
              <tr
                key={id}
                className="border-b border-border/60 last:border-0 hover:bg-white/[0.03] cursor-pointer transition-colors"
                onClick={() => navigate(`/datasets/${id}`)}
              >
                <td className="px-5 py-3 font-bold text-paper flex items-center gap-2">
                  <Database className="w-4 h-4 text-sage shrink-0" />
                  <span>{fileName}</span>
                </td>
                <td className="px-5 py-3 text-muted">
                  <span className="inline-flex items-center gap-1.5 bg-white/5 border border-white/10 px-2 py-0.5 rounded text-xs text-paper">
                    v{version}
                    {totalVersions > 1 && (
                      <span className="text-[10px] text-muted font-normal">
                        ({totalVersions} uploads)
                      </span>
                    )}
                  </span>
                </td>
                <td className="px-5 py-3 text-muted">{uploaded ? new Date(uploaded).toLocaleString() : '—'}</td>
                <td className="px-5 py-3 text-xs text-muted font-mono">#{id}</td>
                <td className="px-5 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                  <div className="inline-flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={(e) => handleDownload(e, id)}
                      disabled={downloadingId === id}
                      className="inline-flex items-center gap-1.5 px-3 py-1 rounded border border-border text-xs text-paper/80 hover:text-sage hover:border-sage/50 transition-colors disabled:opacity-50"
                    >
                      {downloadingId === id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Download className="w-3.5 h-3.5 text-sage" />
                      )}
                      <span>Download</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => navigate(`/datasets/${id}`)}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs text-sage font-medium hover:underline"
                    >
                      View <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
