import axios from 'axios'

// In dev, Vite proxies /api, /upload, /download to http://127.0.0.1:8000 (see vite.config.js).
// In prod, set VITE_API_BASE_URL to the real backend origin, or keep '' and put a reverse proxy in front.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export const client = axios.create({ baseURL: BASE_URL })

const TOKEN_KEY = 'nexus_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}
export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

client.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Normalizes backend/network errors into a small, consistent shape the UI can render.
client.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error?.response?.status
    let message = 'Something went wrong. Please try again.'
    if (!error.response) message = 'Cannot reach the NEXUS backend. Is the API running?'
    else if (status === 401) {
      message = 'Your session has expired. Please log in again.'
      clearToken()
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    else if (status === 403) message = 'You do not have permission to do that.'
    else if (status === 404) message = 'The requested resource was not found.'
    else if (status >= 500) message = 'The server ran into a problem. Please try again shortly.'
    else if (error.response?.data?.message) message = error.response.data.message
    else if (error.response?.data?.detail) {
      message = typeof error.response.data.detail === 'string'
        ? error.response.data.detail
        : JSON.stringify(error.response.data.detail)
    }
    return Promise.reject({ status, message, raw: error })
  }
)

/* ---------------- Auth ---------------- */
export const login = (username, password) =>
  client.post('/api/v1/auth/login', { username, password }).then((r) => r.data)

export const register = (payload) =>
  client.post('/api/v1/auth/register', payload).then((r) => r.data)

export const getCurrentUser = () =>
  client.get('/api/v1/auth/me').then((r) => r.data)

/* ---------------- Users (Admin only) ---------------- */
export const getUsers = () =>
  client.get('/api/v1/users').then((r) => r.data)

export const getUser = (userId) =>
  client.get(`/api/v1/users/${userId}`).then((r) => r.data)

export const updateUserRole = (userId, role) =>
  client.put(`/api/v1/users/${userId}/role`, { role }).then((r) => r.data)

export const updateUserStatus = (userId, status, confirmSelf = false) =>
  client.put(`/api/v1/users/${userId}/status`, { status, confirm_self: confirmSelf }).then((r) => r.data)

/* ---------------- Datasets ---------------- */
export const getDatasets = () =>
  client.get('/api/v1/datasets').then((r) => r.data)

export const getDataset = (datasetId) =>
  client.get(`/api/v1/datasets/${datasetId}`).then((r) => r.data)

/* ---------------- Quality ---------------- */
export const getQuality = (datasetId) =>
  client.get(`/api/v1/quality/${datasetId}`).then((r) => r.data)

/* ---------------- Analytics / KPIs ---------------- */
export const getKPIs = (datasetId) => {
  if (datasetId == null || datasetId === '') {
    return Promise.reject({ status: 400, message: 'dataset_id is required for KPIs' })
  }
  return client.get('/api/v1/kpis', { params: { dataset_id: datasetId } }).then((r) => r.data)
}

/* ---------------- Anomalies ---------------- */
export const getAnomalies = (datasetId) => {
  if (datasetId == null || datasetId === '') {
    return Promise.reject({ status: 400, message: 'dataset_id is required for Anomalies' })
  }
  return client.get('/api/v1/anomalies', { params: { dataset_id: datasetId } }).then((r) => r.data)
}

/* ---------------- Pipelines ---------------- */
export const getPipelines = () =>
  client.get('/api/v1/pipelines').then((r) => r.data)

export const getPipeline = (pipelineId) =>
  client.get(`/api/v1/pipelines/${pipelineId}`).then((r) => r.data)

/* ---------------- Upload / Download ---------------- */
export const uploadDataset = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return client
    .post('/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) onProgress(Math.round((evt.loaded * 100) / evt.total))
      }
    })
    .then((r) => r.data)
}

export const downloadUrl = (filename) => `${BASE_URL}/download/${encodeURIComponent(filename)}`

export async function downloadDatasetFile(datasetId, type = 'clean') {
  const token = getToken()
  const url = `${BASE_URL}/api/v1/datasets/${datasetId}/download/${type}`
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })

  if (!response.ok) {
    let msg = 'Failed to download file'
    try {
      const errJson = await response.json()
      if (errJson?.error) msg = errJson.error
    } catch (_) {}
    throw new Error(msg)
  }

  const blob = await response.blob()
  const contentDisposition = response.headers.get('Content-Disposition')
  let filename = `dataset_${datasetId}_${type}.csv`
  if (contentDisposition) {
    const match = contentDisposition.match(/filename="?([^";]+)"?/)
    if (match && match[1]) filename = match[1]
  }

  const blobUrl = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = blobUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(blobUrl)
}

/* ---------------- Data Correction (Admin / Data Engineer) ---------------- */
export const getDatasetRecords = (datasetId) =>
  client.get(`/api/v1/datasets/${datasetId}/records`).then((r) => r.data)

export const getDatasetAudit = (datasetId) =>
  client.get(`/api/v1/datasets/${datasetId}/audit`).then((r) => r.data)

export const correctDatasetRecord = (datasetId, { row_index, column_name, new_value, source = 'clean' }) =>
  client.post(`/api/v1/datasets/${datasetId}/correct`, { row_index, column_name, new_value, source }).then((r) => r.data)

