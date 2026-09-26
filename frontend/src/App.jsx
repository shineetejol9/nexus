import React from 'react'
import { Routes, Route } from 'react-router-dom'
import ProtectedRoute from './routes/ProtectedRoute.jsx'

import Landing from './pages/Landing.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Datasets from './pages/Datasets.jsx'
import DatasetDetails from './pages/DatasetDetails.jsx'
import Quality from './pages/Quality.jsx'
import Analytics from './pages/Analytics.jsx'
import Anomalies from './pages/Anomalies.jsx'
import Pipelines from './pages/Pipelines.jsx'
import Upload from './pages/Upload.jsx'
import UserManagement from './pages/UserManagement.jsx'
import Settings from './pages/Settings.jsx'

export default function App() {
  return (
    <Routes>
      {/* Public marketing / hero */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Authenticated NEXUS application */}
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/datasets" element={<ProtectedRoute><Datasets /></ProtectedRoute>} />
      <Route path="/datasets/:id" element={<ProtectedRoute><DatasetDetails /></ProtectedRoute>} />
      <Route path="/quality" element={<ProtectedRoute><Quality /></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
      <Route path="/anomalies" element={<ProtectedRoute><Anomalies /></ProtectedRoute>} />
      <Route path="/pipelines" element={<ProtectedRoute><Pipelines /></ProtectedRoute>} />
      <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
      <Route path="/users" element={<ProtectedRoute><UserManagement /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

      <Route path="*" element={<Landing />} />
    </Routes>
  )
}
