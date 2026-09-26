import React, { useEffect, useState } from 'react'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import AppLayout from '../components/AppLayout.jsx'
import QualityCard from '../components/QualityCard.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import EmptyState from '../components/EmptyState.jsx'
import * as api from '../services/api.js'
import { groupDatasetsByFilename } from '../utils/datasetUtils.js'

function list(x) { return Array.isArray(x) ? x : x?.datasets ?? x?.data ?? x?.items ?? [] }
function pct(v) { return v == null ? 0 : v <= 1 ? Math.round(v * 100) : Math.round(v) }

export default function Quality() {
  const [datasets, setDatasets] = useState([])
  const [selected, setSelected] = useState(null)
  const [quality, setQuality] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    (async () => {
      try {
        const res = await api.getDatasets()
        const rawList = list(res)
        const grouped = groupDatasetsByFilename(rawList)
        setDatasets(grouped)
        const firstId = grouped[0]?.dataset_id ?? grouped[0]?.id
        if (firstId != null) setSelected(firstId)
        else setLoading(false)
      } catch (e) {
        setError(e?.message || 'Failed to load datasets.')
        setLoading(false)
      }
    })()
  }, [])

  useEffect(() => {
    if (selected == null) return
    setLoading(true); setError(null); setQuality(null)
    api.getQuality(selected)
      .then((res) => {
        if (res?.error) {
          setQuality(null)
        } else {
          setQuality(res?.data ?? res)
        }
      })
      .catch((e) => {
        if (e?.status === 404 || (typeof e?.message === 'string' && e?.message.toLowerCase().includes('not found'))) {
          setQuality(null)
        } else {
          setError(e?.message || 'Failed to load quality data.')
        }
      })
      .finally(() => setLoading(false))
  }, [selected])

  const q = quality
  const hasReport = q != null && !q.error && (
    q.completeness != null ||
    q.validity != null ||
    q.uniqueness != null ||
    q.consistency != null ||
    q.timeliness != null ||
    q.quality_score != null ||
    q.overall_score != null ||
    q.overall_quality_score != null
  )

  const chartData = hasReport ? [
    { dim: 'Completeness', value: pct(q.completeness) },
    { dim: 'Validity', value: pct(q.validity) },
    { dim: 'Uniqueness', value: pct(q.uniqueness) },
    { dim: 'Consistency', value: pct(q.consistency) },
    { dim: 'Timeliness', value: pct(q.timeliness) }
  ] : []

  return (
    <AppLayout title="Data Quality">
      {datasets.length > 0 && (
        <div className="mb-5 flex items-center gap-3">
          <span className="text-[10px] uppercase tracking-widest text-muted">Dataset</span>
          <select
            value={selected ?? ''}
            onChange={(e) => setSelected(e.target.value)}
            className="bg-panel border border-border rounded-lg px-3 py-2 text-sm text-paper focus:outline-none focus:border-sage/60"
          >
            {datasets.map((d) => {
              const id = d.dataset_id ?? d.id
              return (
                <option key={id} value={id}>
                  {d.file_name ?? d.filename ?? `Dataset ${id}`}
                </option>
              )
            })}
          </select>
        </div>
      )}

      {loading ? (
        <Loading label="Loading quality metrics…" />
      ) : error ? (
        <ErrorMessage message={error} />
      ) : datasets.length === 0 ? (
        <EmptyState title="No datasets to evaluate" hint="Upload a dataset first." />
      ) : !hasReport ? (
        <EmptyState title="No quality report available" hint="No quality metrics have been generated for the selected dataset." />
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
            <QualityCard label="Completeness" value={q.completeness} />
            <QualityCard label="Validity" value={q.validity} />
            <QualityCard label="Uniqueness" value={q.uniqueness} />
            <QualityCard label="Consistency" value={q.consistency} />
            <QualityCard label="Timeliness" value={q.timeliness} />
            <QualityCard label="Overall Score" value={q.quality_score ?? q.overall_score ?? q.overall_quality_score} />
          </div>

          <div className="nx-card p-5 h-[420px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={chartData} outerRadius="70%">
                <PolarGrid stroke="rgba(239,232,218,0.12)" />
                <PolarAngleAxis dataKey="dim" tick={{ fill: '#efe8da99', fontSize: 11 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#efe8da55', fontSize: 10 }} />
                <Radar dataKey="value" stroke="#ff7a2f" fill="#ff7a2f" fillOpacity={0.25} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </AppLayout>
  )
}
