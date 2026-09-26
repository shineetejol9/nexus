import React, { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Rows3, Gauge, Download, Loader2, AlertTriangle, Edit3, CheckCircle2, X } from 'lucide-react'
import AppLayout from '../components/AppLayout.jsx'
import QualityCard from '../components/QualityCard.jsx'
import KPICard from '../components/KPICard.jsx'
import AnomalyTable from '../components/AnomalyTable.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import * as api from '../services/api.js'

function list(x) { return Array.isArray(x) ? x : x?.anomalies ?? x?.data ?? x?.items ?? [] }

export default function DatasetDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { role } = useAuth()
  const canEdit = role === 'Admin' || role === 'Data Engineer'

  const [state, setState] = useState({ loading: true, error: null, dataset: null, quality: null, kpis: null, anomalies: [], allDatasets: [] })
  const [downloadingClean, setDownloadingClean] = useState(false)
  const [downloadingRejected, setDownloadingRejected] = useState(false)
  const [downloadError, setDownloadError] = useState(null)

  // Correction Modal State
  const [showEditModal, setShowEditModal] = useState(false)
  const [editLoading, setEditLoading] = useState(false)
  const [recordsData, setRecordsData] = useState({ clean_rows: [], rejected_rows: [], columns: [] })
  const [activeTab, setActiveTab] = useState('clean') // 'clean' | 'rejected'
  const [selectedRowIndex, setSelectedRowIndex] = useState(null)
  const [selectedColumn, setSelectedColumn] = useState('')
  const [newValue, setNewValue] = useState('')
  const [submittingCorrection, setSubmittingCorrection] = useState(false)
  const [correctionSuccessMsg, setCorrectionSuccessMsg] = useState(null)
  const [correctionErrorMsg, setCorrectionErrorMsg] = useState(null)

  async function load() {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const [dataset, quality, kpis, anomalies, allDs] = await Promise.all([
        api.getDataset(id),
        api.getQuality(id).catch(() => null),
        api.getKPIs(id).catch(() => null),
        api.getAnomalies(id).catch(() => []),
        api.getDatasets().catch(() => [])
      ])
      const dsList = Array.isArray(allDs) ? allDs : allDs?.datasets ?? allDs?.data ?? []
      setState({
        loading: false, error: null,
        dataset: dataset?.data ?? dataset,
        quality: quality?.data ?? quality,
        kpis: kpis?.data ?? kpis,
        anomalies: list(anomalies),
        allDatasets: dsList
      })
    } catch (e) {
      setState((s) => ({ ...s, loading: false, error: e?.message || 'Failed to load dataset.' }))
    }
  }

  useEffect(() => { load() }, [id])

  async function handleDownload(type) {
    const datasetId = state.dataset?.id ?? state.dataset?.dataset_id ?? id
    if (!datasetId) return
    setDownloadError(null)
    if (type === 'clean') setDownloadingClean(true)
    else setDownloadingRejected(true)

    try {
      await api.downloadDatasetFile(datasetId, type)
    } catch (e) {
      setDownloadError(e?.message || `Failed to download ${type} CSV for this dataset.`)
    } finally {
      if (type === 'clean') setDownloadingClean(false)
      else setDownloadingRejected(false)
    }
  }

  async function handleOpenEditModal() {
    setShowEditModal(true)
    setEditLoading(true)
    setCorrectionSuccessMsg(null)
    setCorrectionErrorMsg(null)
    setSelectedRowIndex(null)
    try {
      const data = await api.getDatasetRecords(id)
      setRecordsData(data)
      const cols = data.columns || []
      if (cols.length > 0) setSelectedColumn(cols[0])
    } catch (e) {
      setCorrectionErrorMsg(e?.message || 'Failed to fetch dataset records for correction.')
    } finally {
      setEditLoading(false)
    }
  }

  function handleSelectRow(idx, rowData) {
    setSelectedRowIndex(idx)
    const cols = recordsData.columns || Object.keys(rowData || {})
    const colToUse = selectedColumn && cols.includes(selectedColumn) ? selectedColumn : cols[0] || ''
    setSelectedColumn(colToUse)
    setNewValue(rowData[colToUse] ?? '')
  }

  function handleColumnChange(col) {
    setSelectedColumn(col)
    const rows = activeTab === 'clean' ? recordsData.clean_rows : recordsData.rejected_rows
    if (selectedRowIndex != null && rows[selectedRowIndex]) {
      setNewValue(rows[selectedRowIndex][col] ?? '')
    }
  }

  async function handleSaveCorrection() {
    if (selectedRowIndex == null || !selectedColumn) return
    setSubmittingCorrection(true)
    setCorrectionSuccessMsg(null)
    setCorrectionErrorMsg(null)

    try {
      const res = await api.correctDatasetRecord(id, {
        row_index: selectedRowIndex,
        column_name: selectedColumn,
        new_value: newValue,
        source: activeTab
      })

      const newVer = res.new_version ?? 'new'
      setCorrectionSuccessMsg(`Correction saved. New dataset version created (v${newVer}).`)
      setSelectedRowIndex(null)
      
      // Auto reload after brief pause to navigate to updated version
      setTimeout(() => {
        setShowEditModal(false)
        if (res.dataset_id) {
          navigate(`/datasets/${res.dataset_id}`)
        } else {
          load()
        }
      }, 1500)
    } catch (e) {
      setCorrectionErrorMsg(e?.message || 'Failed to save correction.')
    } finally {
      setSubmittingCorrection(false)
    }
  }

  if (state.loading) return <AppLayout title="Dataset"><Loading label="Loading dataset…" /></AppLayout>
  if (state.error) return <AppLayout title="Dataset"><ErrorMessage message={state.error} onRetry={load} /></AppLayout>

  const d = state.dataset || {}
  const q = state.quality || {}
  const k = state.kpis || {}

  const currentFileName = d.file_name ?? d.filename
  const history = (state.allDatasets || [])
    .filter((item) => {
      const name = item.file_name ?? item.filename
      return name && currentFileName && name.trim().toLowerCase() === currentFileName.trim().toLowerCase()
    })
    .sort((a, b) => (Number(b.version) || 0) - (Number(a.version) || 0) || (Number(b.id ?? b.dataset_id) || 0) - (Number(a.id ?? a.dataset_id) || 0))

  const recordCount =
    (Array.isArray(d.rows) ? d.rows.length : null) ??
    k.kpis?.total_rows ??
    k.total_rows ??
    k.total_records ??
    d.record_count ??
    d.total_records ??
    '—'

  const rawQualityScore =
    q.quality_score ??
    q.overall_score ??
    q.overall_quality_score ??
    k.quality_score ??
    k.kpis?.quality_score ??
    null

  const displayQualityScore =
    rawQualityScore == null || rawQualityScore === '' || isNaN(Number(rawQualityScore))
      ? '—'
      : Math.round(Number(rawQualityScore) <= 1 ? Number(rawQualityScore) * 100 : Number(rawQualityScore))

  const columns = recordsData.columns || []
  const currentTabRows = activeTab === 'clean' ? (recordsData.clean_rows || []) : (recordsData.rejected_rows || [])
  const selectedRowData = selectedRowIndex != null ? currentTabRows[selectedRowIndex] : null

  return (
    <AppLayout title={`Dataset ${id}`}>
      <Link to="/datasets" className="inline-flex items-center gap-2 text-xs text-muted hover:text-sage mb-5 transition-colors">
        <ArrowLeft className="w-3.5 h-3.5" /> Back to datasets
      </Link>

      <div className="nx-card p-5 mb-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div><p className="text-[10px] uppercase tracking-widest text-muted mb-1">Dataset ID</p><p className="font-bold text-paper">{d.dataset_id ?? d.id ?? id}</p></div>
        <div><p className="text-[10px] uppercase tracking-widest text-muted mb-1">File Name</p><p className="text-paper">{d.file_name ?? d.filename ?? '—'}</p></div>
        <div>
          <p className="text-[10px] uppercase tracking-widest text-muted mb-1">Version</p>
          {history.length > 1 ? (
            <select
              value={d.id ?? d.dataset_id ?? id}
              onChange={(e) => navigate(`/datasets/${e.target.value}`)}
              className="bg-panel border border-border/80 rounded px-2 py-0.5 text-xs text-paper focus:outline-none focus:border-sage/60 cursor-pointer"
            >
              {history.map((h) => {
                const hId = h.id ?? h.dataset_id
                const isLatest = String(hId) === String(history[0]?.id ?? history[0]?.dataset_id)
                return (
                  <option key={hId} value={hId}>
                    v{h.version ?? '—'} {isLatest ? '(Latest)' : ''}
                  </option>
                )
              })}
            </select>
          ) : (
            <p className="text-paper">v{d.version ?? '—'}</p>
          )}
        </div>
        <div><p className="text-[10px] uppercase tracking-widest text-muted mb-1">Uploaded</p><p className="text-paper">{d.upload_date ?? d.uploaded_at ? new Date(d.upload_date ?? d.uploaded_at).toLocaleString() : '—'}</p></div>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-6">
        <button
          onClick={() => handleDownload('clean')}
          disabled={downloadingClean}
          className="inline-flex items-center gap-2 text-xs uppercase tracking-widest px-4 py-2 rounded-lg border border-border hover:border-sage/50 hover:text-sage transition-colors text-paper disabled:opacity-50"
        >
          {downloadingClean ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5 text-sage" />}
          Download Clean CSV
        </button>

        <button
          onClick={() => handleDownload('rejected')}
          disabled={downloadingRejected}
          className="inline-flex items-center gap-2 text-xs uppercase tracking-widest px-4 py-2 rounded-lg border border-border hover:border-toad/50 hover:text-toad transition-colors text-paper disabled:opacity-50"
        >
          {downloadingRejected ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5 text-toad" />}
          Download Rejected CSV
        </button>

        {canEdit && (
          <button
            onClick={handleOpenEditModal}
            className="inline-flex items-center gap-2 text-xs uppercase tracking-widest px-4 py-2 rounded-lg border border-volt/40 bg-volt/10 text-volt hover:bg-volt/20 hover:border-volt transition-colors font-semibold"
          >
            <Edit3 className="w-3.5 h-3.5 text-volt" />
            Edit / Correct Data
          </button>
        )}
      </div>

      {downloadError && (
        <div className="mb-6 flex items-center gap-2 text-sm text-toad bg-toad/10 border border-toad/30 rounded-lg px-4 py-3">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {downloadError}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        <KPICard label="Record Count" value={recordCount} icon={Rows3} accent="volt" />
        <KPICard label="Quality Score" value={displayQualityScore} suffix={displayQualityScore === '—' ? '' : '%'} icon={Gauge} accent="sage" />
        <KPICard label="Anomalies" value={state.anomalies.length} accent="toad" />
      </div>

      <h2 className="font-disp text-lg tracking-wide uppercase text-muted mb-3">Quality Dimensions</h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
        <QualityCard label="Completeness" value={q.completeness} />
        <QualityCard label="Validity" value={q.validity} />
        <QualityCard label="Uniqueness" value={q.uniqueness} />
        <QualityCard label="Consistency" value={q.consistency} />
        <QualityCard label="Timeliness" value={q.timeliness} />
        <QualityCard label="Overall" value={rawQualityScore} />
      </div>

      <h2 className="font-disp text-lg tracking-wide uppercase text-muted mb-3">Anomalies</h2>
      {state.anomalies.length === 0 ? (
        <EmptyState title="No anomalies detected for this dataset" />
      ) : (
        <AnomalyTable anomalies={state.anomalies} />
      )}

      {/* Edit / Correct Data Modal */}
      {showEditModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-panel border border-border rounded-xl max-w-4xl w-full p-6 shadow-2xl space-y-5 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-border pb-3 shrink-0">
              <div>
                <h3 className="font-disp text-lg uppercase tracking-wide text-paper flex items-center gap-2">
                  <Edit3 className="w-4 h-4 text-volt" /> Edit / Correct Data
                </h3>
                <p className="text-xs text-muted mt-0.5">
                  Saving a correction validates the dataset, re-runs the processing pipeline, and creates a new dataset version.
                </p>
              </div>
              <button onClick={() => setShowEditModal(false)} className="text-muted hover:text-paper">
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Feedback Alerts */}
            {correctionSuccessMsg && (
              <div className="p-3 bg-sage/15 border border-sage/30 rounded-lg text-xs text-sage flex items-center gap-2 shrink-0">
                <CheckCircle2 className="w-4 h-4 shrink-0" /> {correctionSuccessMsg}
              </div>
            )}

            {correctionErrorMsg && (
              <div className="p-3 bg-toad/15 border border-toad/30 rounded-lg text-xs text-toad flex items-center gap-2 shrink-0">
                <AlertTriangle className="w-4 h-4 shrink-0" /> {correctionErrorMsg}
              </div>
            )}

            {editLoading ? (
              <div className="py-12 flex justify-center"><Loading label="Loading dataset records for correction…" /></div>
            ) : (
              <div className="space-y-4 overflow-y-auto flex-1 pr-1">
                {/* Source Tabs */}
                <div className="flex items-center gap-2 border-b border-border text-xs">
                  <button
                    onClick={() => { setActiveTab('clean'); setSelectedRowIndex(null); }}
                    className={`px-4 py-2 border-b-2 font-medium transition-colors ${
                      activeTab === 'clean' ? 'border-sage text-sage' : 'border-transparent text-muted hover:text-paper'
                    }`}
                  >
                    Clean Records ({recordsData?.clean_rows?.length || 0})
                  </button>
                  <button
                    onClick={() => { setActiveTab('rejected'); setSelectedRowIndex(null); }}
                    className={`px-4 py-2 border-b-2 font-medium transition-colors ${
                      activeTab === 'rejected' ? 'border-toad text-toad' : 'border-transparent text-muted hover:text-paper'
                    }`}
                  >
                    Rejected Records ({recordsData?.rejected_rows?.length || 0})
                  </button>
                </div>

                {/* Table of Records */}
                {currentTabRows.length === 0 ? (
                  <EmptyState title={`No ${activeTab} records found in this dataset version.`} />
                ) : (
                  <div className="border border-border/80 rounded-lg overflow-x-auto max-h-48">
                    <table className="w-full text-xs text-left">
                      <thead className="bg-ink/60 uppercase tracking-widest text-muted border-b border-border sticky top-0">
                        <tr>
                          <th className="p-2 border-r border-border">#</th>
                          {columns.map((col) => (
                            <th key={col} className="p-2 border-r border-border">{col}</th>
                          ))}
                          <th className="p-2">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {currentTabRows.map((row, idx) => {
                          const isSelected = selectedRowIndex === idx
                          return (
                            <tr key={idx} className={`border-b border-border/40 ${isSelected ? 'bg-volt/10' : 'hover:bg-white/[0.03]'}`}>
                              <td className="p-2 font-mono text-muted border-r border-border">{idx + 1}</td>
                              {columns.map((col) => (
                                <td key={col} className="p-2 border-r border-border text-paper">{String(row[col] ?? '')}</td>
                              ))}
                              <td className="p-2">
                                <button
                                  onClick={() => handleSelectRow(idx, row)}
                                  className="px-2 py-1 bg-volt/20 text-volt hover:bg-volt/30 rounded border border-volt/40 text-[10px] uppercase font-bold"
                                >
                                  {isSelected ? 'Editing' : 'Select'}
                                </button>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Form Editor when a row is selected */}
                {selectedRowIndex != null && selectedRowData && (
                  <div className="bg-ink/60 border border-volt/30 rounded-lg p-4 space-y-3">
                    <h4 className="font-bold text-xs uppercase text-paper tracking-wider flex items-center justify-between">
                      <span>Edit Record #{selectedRowIndex + 1} ({activeTab})</span>
                      <span className="text-[10px] text-volt">Creates Version {Number(d.version || 1) + 1}</span>
                    </h4>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                      <div>
                        <label className="block text-muted text-[10px] uppercase tracking-widest mb-1">Column</label>
                        <select
                          value={selectedColumn}
                          onChange={(e) => handleColumnChange(e.target.value)}
                          className="w-full bg-panel border border-border rounded px-3 py-1.5 text-paper focus:outline-none focus:border-volt"
                        >
                          {columns.map((col) => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-muted text-[10px] uppercase tracking-widest mb-1">Current Value</label>
                        <input
                          type="text"
                          readOnly
                          value={selectedRowData[selectedColumn] ?? ''}
                          className="w-full bg-panel/50 border border-border/60 rounded px-3 py-1.5 text-muted cursor-not-allowed"
                        />
                      </div>

                      <div>
                        <label className="block text-muted text-[10px] uppercase tracking-widest mb-1">New Value</label>
                        <input
                          type="text"
                          value={newValue}
                          onChange={(e) => setNewValue(e.target.value)}
                          placeholder="Enter corrected value..."
                          className="w-full bg-panel border border-volt/60 rounded px-3 py-1.5 text-paper focus:outline-none focus:border-volt"
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-end gap-3 pt-2">
                      <button
                        type="button"
                        onClick={() => setSelectedRowIndex(null)}
                        className="px-4 py-1.5 text-xs uppercase tracking-widest rounded border border-border text-paper hover:bg-white/5"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={handleSaveCorrection}
                        disabled={submittingCorrection}
                        className="px-4 py-1.5 text-xs uppercase tracking-widest font-bold rounded bg-volt text-ink hover:brightness-110 disabled:opacity-50 flex items-center gap-1.5 shadow-glow"
                      >
                        {submittingCorrection ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                        Save Correction
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </AppLayout>
  )
}
