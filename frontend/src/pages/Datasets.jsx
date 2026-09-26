import React, { useEffect, useState } from 'react'
import AppLayout from '../components/AppLayout.jsx'
import DatasetTable from '../components/DatasetTable.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import EmptyState from '../components/EmptyState.jsx'
import * as api from '../services/api.js'
import { groupDatasetsByFilename } from '../utils/datasetUtils.js'

export { groupDatasetsByFilename }


export default function Datasets() {
  const [datasets, setDatasets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function load() {
    setLoading(true); setError(null)
    try {
      const res = await api.getDatasets()
      const rawList = Array.isArray(res) ? res : res?.datasets ?? res?.data ?? []
      const grouped = groupDatasetsByFilename(rawList)
      setDatasets(grouped)
    } catch (e) {
      setError(e?.message || 'Failed to load datasets.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <AppLayout title="Datasets">
      {loading ? (
        <Loading label="Loading datasets…" />
      ) : error ? (
        <ErrorMessage message={error} onRetry={load} />
      ) : datasets.length === 0 ? (
        <EmptyState title="No datasets found" hint="Upload a CSV to create your first dataset." />
      ) : (
        <DatasetTable datasets={datasets} />
      )}
    </AppLayout>
  )
}
