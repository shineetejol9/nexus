import React, { useEffect, useState } from 'react'
import { Database, Rows3, CheckCircle2, XCircle, Gauge, AlertTriangle, Workflow } from 'lucide-react'
import AppLayout from '../components/AppLayout.jsx'
import KPICard from '../components/KPICard.jsx'
import QualityCard from '../components/QualityCard.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import EmptyState from '../components/EmptyState.jsx'
import * as api from '../services/api.js'

function extractDatasets(x) {
  if (Array.isArray(x)) return x
  return x?.datasets ?? x?.data ?? x?.items ?? []
}

function extractPipelines(x) {
  if (Array.isArray(x)) return x
  return x?.pipelines ?? x?.data ?? x?.items ?? []
}

function extractAnomalies(x) {
  if (Array.isArray(x)) return x
  return x?.anomalies ?? x?.data ?? x?.items ?? []
}

function num(...vals) { for (const v of vals) if (typeof v === 'number') return v; return null }

export default function Dashboard() {
  const [state, setState] = useState({ loading: true, error: null, datasets: [], pipelines: [], anomalies: [], kpis: null, quality: null })

  async function load() {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      // 1. First fetch /api/v1/datasets and /api/v1/pipelines
      const [datasetsRes, pipelinesRes] = await Promise.all([
        api.getDatasets(),
        api.getPipelines().catch(() => [])
      ])

      // 2. Correctly read the datasets & pipelines arrays from responses
      const datasets = extractDatasets(datasetsRes)
      const pipelines = extractPipelines(pipelinesRes)

      // 5. If no datasets exist, do NOT call KPI or anomaly endpoints. Show existing empty state.
      if (datasets.length === 0) {
        setState({ loading: false, error: null, datasets: [], pipelines, anomalies: [], kpis: null, quality: null })
        return
      }

      // 3. Obtain a valid dataset ID from the first dataset
      const firstId = datasets[0]?.id ?? datasets[0]?.dataset_id

      let kpis = null
      let quality = null
      let anomaliesRes = null

      // 4. Only then call /api/v1/kpis?dataset_id=ID, /api/v1/anomalies?dataset_id=ID, /api/v1/quality/ID
      if (firstId != null) {
        const [kRes, qRes, aRes] = await Promise.all([
          api.getKPIs(firstId).catch(() => null),
          api.getQuality(firstId).catch(() => null),
          api.getAnomalies(firstId).catch(() => null)
        ])
        kpis = kRes
        quality = qRes
        anomaliesRes = aRes
      }

      const anomalies = extractAnomalies(anomaliesRes)

      setState({ loading: false, error: null, datasets, pipelines, anomalies, kpis, quality })
    } catch (e) {
      setState((s) => ({ ...s, loading: false, error: e?.message || 'Failed to load dashboard data.' }))
    }
  }

  useEffect(() => { load() }, [])

  if (state.loading) return <AppLayout title="Overview"><Loading label="Loading dashboard…" /></AppLayout>
  if (state.error) return <AppLayout title="Overview"><ErrorMessage message={state.error} onRetry={load} /></AppLayout>

  const { datasets, pipelines, anomalies, kpis, quality } = state
  const k = kpis?.kpis ?? kpis?.data ?? kpis ?? {}
  const q = quality?.data ?? quality ?? {}

  const firstId = datasets[0]?.id ?? datasets[0]?.dataset_id
  const targetPipeline = pipelines.find((p) => String(p.dataset_id) === String(firstId)) || pipelines[0]

  const totalRecords = num(k.total_records, k.total_rows, targetPipeline?.total_rows)
  const cleanRecords = num(
    k.clean_records,
    k.clean_rows,
    targetPipeline?.clean_rows,
    pipelines.length > 0 ? pipelines.reduce((sum, p) => sum + (typeof p.clean_rows === 'number' ? p.clean_rows : 0), 0) : null
  )
  const badRecords = num(
    k.bad_records,
    k.bad_rows,
    targetPipeline?.bad_rows,
    pipelines.length > 0 ? pipelines.reduce((sum, p) => sum + (typeof p.bad_rows === 'number' ? p.bad_rows : 0), 0) : null
  )
  const qualityScore = num(k.quality_score, q.overall_score, q.overall_quality_score, q.quality_score)
  const displayQualityScore =
    qualityScore == null || isNaN(Number(qualityScore))
      ? '—'
      : Math.round(Number(qualityScore) <= 1 ? Number(qualityScore) * 100 : Number(qualityScore))

  return (
    <AppLayout title="Overview">
      {datasets.length === 0 ? (
        <EmptyState
          title="No datasets yet"
          hint="Upload a CSV to start seeing KPIs, quality scores and pipeline activity here."
        />
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <KPICard label="Total Datasets" value={datasets.length} icon={Database} accent="sage" />
            <KPICard label="Total Records" value={totalRecords ?? '—'} icon={Rows3} accent="volt" />
            <KPICard label="Clean Records" value={cleanRecords ?? '—'} icon={CheckCircle2} accent="sage" />
            <KPICard label="Bad Records" value={badRecords ?? '—'} icon={XCircle} accent="toad" />
            <KPICard label="Quality Score" value={displayQualityScore} suffix={displayQualityScore === '—' ? '' : '%'} icon={Gauge} accent="volt" />
            <KPICard label="Anomalies" value={anomalies.length} icon={AlertTriangle} accent="toad" />
            <KPICard label="Pipelines" value={pipelines.length} icon={Workflow} accent="sage" />
          </div>

          <h2 className="font-disp text-lg tracking-wide uppercase text-muted mb-3">Quality Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-8">
            <QualityCard label="Completeness" value={q.completeness} />
            <QualityCard label="Validity" value={q.validity} />
            <QualityCard label="Uniqueness" value={q.uniqueness} />
            <QualityCard label="Consistency" value={q.consistency} />
            <QualityCard label="Timeliness" value={q.timeliness} />
            <QualityCard label="Overall Score" value={q.quality_score ?? q.overall_score ?? q.overall_quality_score} />
          </div>

          <h2 className="font-disp text-lg tracking-wide uppercase text-muted mb-3">Recent Pipelines</h2>
          {pipelines.length === 0 ? (
            <EmptyState title="No pipeline runs yet" />
          ) : (
            <div className="nx-card overflow-x-auto">
              <table className="w-full text-sm">
                <tbody>
                  {pipelines.slice(0, 5).map((p) => (
                    <tr key={p.pipeline_id ?? p.id} className="border-b border-border/60 last:border-0">
                      <td className="px-5 py-3 font-bold text-paper">{p.pipeline_id ?? p.id}</td>
                      <td className="px-5 py-3 text-muted">dataset {p.dataset_id}</td>
                      <td className="px-5 py-3">
                        <span className="nx-badge border border-white/10 text-muted">{(p.status || 'UNKNOWN').toUpperCase()}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </AppLayout>
  )
}
