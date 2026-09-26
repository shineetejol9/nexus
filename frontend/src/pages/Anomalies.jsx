import React, { useEffect, useState } from 'react'
import AppLayout from '../components/AppLayout.jsx'
import AnomalyTable from '../components/AnomalyTable.jsx'
import KPICard from '../components/KPICard.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import EmptyState from '../components/EmptyState.jsx'
import * as api from '../services/api.js'
import { groupDatasetsByFilename } from '../utils/datasetUtils.js'
import { AlertTriangle } from 'lucide-react'

function extractDatasets(x) { return Array.isArray(x) ? x : x?.datasets ?? x?.data ?? x?.items ?? [] }
function extractAnomalies(x) { return Array.isArray(x) ? x : x?.anomalies ?? x?.data ?? x?.items ?? [] }

export default function Anomalies() {
  const [datasets, setDatasets] = useState([])
  const [selected, setSelected] = useState('')
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getDatasets()
      .then((res) => {
        const rawList = extractDatasets(res)
        const grouped = groupDatasetsByFilename(rawList)
        setDatasets(grouped)
      })
      .catch(() => {})
  }, [])

  async function load() {
    setLoading(true); setError(null)
    try {
      if (!selected) {
        if (datasets.length === 0) {
          setAnomalies([])
          return
        }
        const results = await Promise.all(
          datasets.map(async (d) => {
            const id = d.dataset_id ?? d.id
            if (!id) return []
            try {
              const res = await api.getAnomalies(id)
              return extractAnomalies(res)
            } catch (_) {
              return []
            }
          })
        )
        setAnomalies(results.flat())
      } else {
        const res = await api.getAnomalies(selected)
        setAnomalies(extractAnomalies(res))
      }
    } catch (e) {
      setError(e?.message || 'Failed to load anomalies.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [selected, datasets])

  return (
    <AppLayout title="Anomalies">
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <KPICard label="Total Anomalies" value={anomalies.length} icon={AlertTriangle} accent="toad" />
        {datasets.length > 0 && (
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            className="bg-panel border border-border rounded-lg px-3 py-2 text-sm text-paper focus:outline-none focus:border-sage/60 h-fit self-center"
          >
            <option value="">All datasets</option>
            {datasets.map((d) => (
              <option key={d.dataset_id ?? d.id} value={d.dataset_id ?? d.id}>
                {d.file_name ?? d.filename ?? `Dataset ${d.dataset_id ?? d.id}`}
              </option>
            ))}
          </select>
        )}
      </div>

      {loading ? (
        <Loading label="Scanning for anomalies…" />
      ) : error ? (
        <ErrorMessage message={error} onRetry={load} />
      ) : anomalies.length === 0 ? (
        <EmptyState title="No anomalies detected" hint="Great news — the selected data is within expected bounds." />
      ) : (
        <AnomalyTable anomalies={anomalies} />
      )}
    </AppLayout>
  )
}
