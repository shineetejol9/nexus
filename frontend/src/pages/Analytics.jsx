import React, { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import AppLayout from '../components/AppLayout.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import EmptyState from '../components/EmptyState.jsx'
import * as api from '../services/api.js'
import { groupDatasetsByFilename } from '../utils/datasetUtils.js'

function list(x) { return Array.isArray(x) ? x : x?.datasets ?? x?.data ?? x?.items ?? [] }
const COLOR_MAP = {
  'Clean Records': '#ff7a2f',
  'Bad Records': '#c8372d'
}

export default function Analytics() {
  const [datasets, setDatasets] = useState([])
  const [rows, setRows] = useState([])   // [{ name, clean, bad }] per dataset
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function load() {
    setLoading(true); setError(null)
    try {
      const [dsRes, pipeRes] = await Promise.all([
        api.getDatasets(),
        api.getPipelines().catch(() => [])
      ])
      const rawList = list(dsRes)
      const ds = groupDatasetsByFilename(rawList)
      setDatasets(ds)

      const pipelines = Array.isArray(pipeRes) ? pipeRes : pipeRes?.pipelines ?? pipeRes?.data ?? []

      const kpiRows = await Promise.all(
        ds.map(async (d) => {
          const id = d.dataset_id ?? d.id
          const name = d.file_name ?? d.filename ?? `Dataset ${id}`

          const pipe = pipelines.find((p) => String(p.dataset_id) === String(id) || String(p.id) === String(id))

          let clean = pipe?.clean_rows
          let bad = pipe?.bad_rows

          if (clean == null || bad == null) {
            const kpis = id ? await api.getKPIs(id).catch(() => null) : null
            const k = kpis?.kpis ?? kpis?.data ?? kpis ?? {}
            clean = clean ?? k.clean_records ?? k.clean_rows ?? k.total_rows ?? (Array.isArray(d.rows) ? d.rows.length : 0)
            bad = bad ?? k.bad_records ?? k.bad_rows ?? 0
          }

          return {
            name,
            clean: Number(clean) || 0,
            bad: Number(bad) || 0
          }
        })
      )
      setRows(kpiRows)
    } catch (e) {
      setError(e?.message || 'Failed to load analytics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const totalClean = rows.reduce((a, r) => a + (r.clean || 0), 0)
  const totalBad = rows.reduce((a, r) => a + (r.bad || 0), 0)
  const pieData = [
    { name: 'Clean Records', value: totalClean },
    { name: 'Bad Records', value: totalBad }
  ].filter((p) => p.value > 0)

  return (
    <AppLayout title="Analytics">
      {loading ? (
        <Loading label="Crunching numbers…" />
      ) : error ? (
        <ErrorMessage message={error} onRetry={load} />
      ) : datasets.length === 0 ? (
        <EmptyState title="No data to analyze yet" hint="Upload a dataset to unlock analytics." />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 nx-card p-5 h-[420px]">
            <p className="text-[11px] uppercase tracking-widest text-muted mb-4">Clean vs. Bad Records by Dataset</p>
            <ResponsiveContainer width="100%" height="90%">
              <BarChart data={rows}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(239,232,218,0.08)" />
                <XAxis dataKey="name" tick={{ fill: '#efe8da99', fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={60} />
                <YAxis tick={{ fill: '#efe8da99', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#0d1114', border: '1px solid rgba(239,232,218,0.12)', borderRadius: 8 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="clean" name="Clean Records" stackId="a" fill="#ff7a2f" radius={[0, 0, 0, 0]} />
                <Bar dataKey="bad" name="Bad Records" stackId="a" fill="#c8372d" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="nx-card p-5 h-[420px]">
            <p className="text-[11px] uppercase tracking-widest text-muted mb-4">Overall Record Split</p>
            {pieData.length === 0 ? (
              <EmptyState title="No KPI data yet" />
            ) : (
              <ResponsiveContainer width="100%" height="90%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={95} paddingAngle={3}>
                    {pieData.map((entry) => (
                      <Cell key={entry.name} fill={COLOR_MAP[entry.name] || '#ff7a2f'} />
                    ))}
                  </Pie>
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#0d1114', border: '1px solid rgba(239,232,218,0.12)', borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      )}
    </AppLayout>
  )
}
