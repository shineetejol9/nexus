import React, { useEffect, useState } from 'react'
import AppLayout from '../components/AppLayout.jsx'
import PipelineTable from '../components/PipelineTable.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import EmptyState from '../components/EmptyState.jsx'
import * as api from '../services/api.js'

function list(x) { return Array.isArray(x) ? x : x?.pipelines ?? x?.data ?? x?.items ?? [] }

export default function Pipelines() {
  const [pipelines, setPipelines] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function load() {
    setLoading(true); setError(null)
    try {
      const res = await api.getPipelines()
      setPipelines(list(res))
    } catch (e) {
      setError(e?.message || 'Failed to load pipelines.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <AppLayout title="Pipelines">
      {loading ? (
        <Loading label="Loading pipelines…" />
      ) : error ? (
        <ErrorMessage message={error} onRetry={load} />
      ) : pipelines.length === 0 ? (
        <EmptyState title="No pipeline runs yet" hint="Pipelines are created automatically when you upload a dataset." />
      ) : (
        <PipelineTable pipelines={pipelines} />
      )}
    </AppLayout>
  )
}
