import React, { useCallback, useState } from 'react'
import { UploadCloud, FileText, Loader2, CheckCircle2, AlertTriangle, Download } from 'lucide-react'
import AppLayout from '../components/AppLayout.jsx'
import KPICard from '../components/KPICard.jsx'
import Loading from '../components/Loading.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import * as api from '../services/api.js'

export default function Upload() {
  const { role: currentRole, loading: authLoading } = useAuth()
  const [file, setFile] = useState(null)
  const [dragOver, setDragOver] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('idle') // idle | uploading | success | error
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) { setFile(f); setStatus('idle'); setResult(null); setError(null) }
  }, [])

  const onBrowse = (e) => {
    const f = e.target.files?.[0]
    if (f) { setFile(f); setStatus('idle'); setResult(null); setError(null) }
  }

  async function handleUpload() {
    if (!file) return
    setStatus('uploading'); setError(null); setProgress(0)
    try {
      const res = await api.uploadDataset(file, setProgress)
      setResult(res?.data ?? res)
      setStatus('success')
    } catch (e) {
      setError(e?.message || 'Upload failed. Please try again.')
      setStatus('error')
    }
  }

  if (authLoading) {
    return (
      <AppLayout title="Upload Data">
        <Loading label="Verifying session…" />
      </AppLayout>
    )
  }

  if (currentRole && !['Admin', 'Data Engineer', 'Viewer'].includes(currentRole)) {
    return (
      <AppLayout title="Upload Data">
        <div className="nx-card p-6 max-w-lg">
          <div className="flex items-center gap-3 text-toad">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <div>
              <h2 className="font-bold text-paper">Access Denied</h2>
              <p className="text-xs text-muted mt-1">Sufficient privileges are required to upload datasets.</p>
            </div>
          </div>
        </div>
      </AppLayout>
    )
  }

  const r = result || {}
  const totalRows = (r.clean_rows ?? 0) + (r.bad_rows ?? 0) || r.database_rows || '—'
  const qualityScorePct = r.quality_score != null
    ? (r.quality_score <= 1 ? Math.round(r.quality_score * 100) : Math.round(r.quality_score))
    : '—'

  return (
    <AppLayout title="Upload Data">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`nx-card border-dashed p-10 flex flex-col items-center justify-center text-center gap-3 transition-colors
          ${dragOver ? 'border-sage/60 bg-sage/5' : 'border-white/15'}`}
      >
        <UploadCloud className={`w-10 h-10 ${dragOver ? 'text-sage' : 'text-muted'}`} />
        <p className="text-sm text-paper">Drag & drop a CSV file here</p>
        <p className="text-xs text-muted">or</p>
        <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-border text-xs uppercase tracking-widest hover:border-sage/50 hover:text-sage transition-colors">
          Browse file
          <input type="file" accept=".csv" className="hidden" onChange={onBrowse} />
        </label>

        {file && (
          <div className="mt-3 flex items-center gap-2 text-sm text-paper/90">
            <FileText className="w-4 h-4 text-volt" /> {file.name}
          </div>
        )}
      </div>

      <div className="mt-5 flex items-center gap-4">
        <button
          onClick={handleUpload}
          disabled={!file || status === 'uploading'}
          className="flex items-center gap-2 bg-sage text-ink font-bold text-sm tracking-widest uppercase px-6 py-3 rounded-lg
            hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-glow"
        >
          {status === 'uploading' ? <Loader2 className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
          {status === 'uploading' ? `Uploading… ${progress}%` : 'Upload Dataset'}
        </button>

        {status === 'uploading' && (
          <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden max-w-xs">
            <div className="h-full bg-volt transition-all duration-200" style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>

      {status === 'error' && (
        <div className="mt-5 flex items-center gap-2 text-sm text-toad bg-toad/10 border border-toad/30 rounded-lg px-4 py-3">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {status === 'success' && (
        <div className="mt-8">
          <div className="flex items-center gap-2 text-sage mb-4 text-sm font-semibold">
            <CheckCircle2 className="w-5 h-5 shrink-0" /> Upload complete — pipeline processed successfully.
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <KPICard label="Dataset ID" value={r.dataset_id ?? '—'} accent="volt" />
            <KPICard label="Filename" value={r.filename ?? file?.name ?? '—'} accent="sage" />
            <KPICard label="Version" value={r.version != null ? `v${r.version}` : '—'} accent="volt" />
            <KPICard label="Total Rows" value={totalRows} accent="sage" />
            <KPICard label="Clean Rows" value={r.clean_rows ?? '—'} accent="sage" />
            <KPICard label="Bad Rows" value={r.bad_rows ?? '—'} accent="toad" />
            <KPICard label="Quality Score" value={qualityScorePct} suffix={qualityScorePct !== '—' ? '%' : ''} accent="volt" />
            <KPICard label="Pipeline ID" value={r.pipeline_id ?? '—'} accent="sage" />
          </div>
          {r.download_file || r.cleaned_file_name || r.output_file ? (
            <a
              href={api.downloadUrl(r.download_file || r.cleaned_file_name || r.output_file)}
              className="mt-4 inline-flex items-center gap-2 text-xs uppercase tracking-widest px-4 py-2 rounded-lg border border-border hover:border-sage/50 hover:text-sage transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> Download cleaned CSV
            </a>
          ) : null}
        </div>
      )}
    </AppLayout>
  )
}
