import React, { useEffect, useState } from 'react'
import {
  ShieldAlert, Eye, Shield, UserCheck, UserX, X,
  Clock, Database, Workflow, AlertTriangle, CheckCircle2, User, Activity
} from 'lucide-react'
import AppLayout from '../components/AppLayout.jsx'
import Loading from '../components/Loading.jsx'
import ErrorMessage from '../components/ErrorMessage.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import * as api from '../services/api.js'

function RoleBadge({ role }) {
  const r = (role || '').trim()
  const map = {
    Admin: 'bg-sage/15 text-sage border-sage/30',
    'Data Engineer': 'bg-volt/15 text-volt border-volt/30',
    Viewer: 'bg-white/10 text-paper/80 border-white/15'
  }
  return (
    <span className={`nx-badge border ${map[r] || 'bg-white/10 text-muted border-white/10'}`}>
      {r || 'Unknown'}
    </span>
  )
}

function StatusBadge({ status }) {
  const s = (status || 'active').toLowerCase()
  const isAct = s === 'active'
  return (
    <span className={`nx-badge border inline-flex items-center gap-1.5 ${
      isAct
        ? 'bg-sage/15 text-sage border-sage/30'
        : 'bg-toad/15 text-toad border-toad/30'
    }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${isAct ? 'bg-sage animate-pulse' : 'bg-toad'}`} />
      <span className="capitalize">{s}</span>
    </span>
  )
}

function formatDate(val) {
  if (!val) return '—'
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return String(val)
    return d.toLocaleString()
  } catch {
    return String(val)
  }
}

export default function UserManagement() {
  const { user: currentUser, role: currentRole } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [feedback, setFeedback] = useState(null)

  // Modals state
  const [viewingUser, setViewingUser] = useState(null)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [detailsData, setDetailsData] = useState(null)

  const [roleModalUser, setRoleModalUser] = useState(null)
  const [selectedRole, setSelectedRole] = useState('')
  const [submittingRole, setSubmittingRole] = useState(false)

  const [statusModalUser, setStatusModalUser] = useState(null)
  const [confirmSelfDeactivate, setConfirmSelfDeactivate] = useState(false)
  const [submittingStatus, setSubmittingStatus] = useState(false)

  const currentUserId = currentUser?.user_id ?? currentUser?.id

  async function load() {
    if (currentRole !== 'Admin') {
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await api.getUsers()
      const list = Array.isArray(res) ? res : res?.users ?? res?.data ?? []
      setUsers(list)
    } catch (err) {
      setError(err?.message || 'Failed to load users.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (currentRole) {
      load()
    }
  }, [currentRole])

  // Open Details Modal
  async function handleOpenDetails(user) {
    setViewingUser(user)
    setDetailsLoading(true)
    setDetailsData(null)
    try {
      const res = await api.getUser(user.id)
      setDetailsData(res)
    } catch (err) {
      setDetailsData({
        user,
        datasets: [],
        pipelines: [],
        recent_activity: [],
        ownership_note: 'Failed to load extended activity: ' + (err?.message || 'Network error')
      })
    } finally {
      setDetailsLoading(false)
    }
  }

  // Open Role Modal
  function handleOpenRoleModal(user) {
    setRoleModalUser(user)
    setSelectedRole(user.role)
  }

  // Submit Role Change
  async function handleSubmitRole(e) {
    e.preventDefault()
    if (!roleModalUser || !selectedRole) return
    setSubmittingRole(true)
    try {
      await api.updateUserRole(roleModalUser.id, selectedRole)
      setFeedback({ type: 'success', text: `Role for ${roleModalUser.username} successfully updated to ${selectedRole}.` })
      setRoleModalUser(null)
      load()
    } catch (err) {
      setFeedback({ type: 'error', text: err?.message || 'Failed to update user role.' })
    } finally {
      setSubmittingRole(false)
    }
  }

  // Open Status Modal (Activate / Deactivate)
  function handleOpenStatusModal(user) {
    setStatusModalUser(user)
    setConfirmSelfDeactivate(false)
  }

  // Submit Status Change
  async function handleSubmitStatus() {
    if (!statusModalUser) return
    const targetStatus = (statusModalUser.status || 'active') === 'active' ? 'inactive' : 'active'
    const isSelf = currentUserId === statusModalUser.id || currentUser?.username === statusModalUser.username

    if (targetStatus === 'inactive' && isSelf && !confirmSelfDeactivate) {
      return
    }

    setSubmittingStatus(true)
    try {
      await api.updateUserStatus(statusModalUser.id, targetStatus, isSelf)
      setFeedback({
        type: 'success',
        text: `User ${statusModalUser.username} has been ${targetStatus === 'active' ? 'reactivated' : 'deactivated'}.`
      })
      setStatusModalUser(null)
      load()
    } catch (err) {
      setFeedback({ type: 'error', text: err?.message || 'Failed to update user status.' })
    } finally {
      setSubmittingStatus(false)
    }
  }

  if (currentRole && currentRole !== 'Admin') {
    return (
      <AppLayout title="User Management">
        <div className="nx-card p-6 max-w-lg">
          <div className="flex items-center gap-3 text-toad">
            <ShieldAlert className="w-5 h-5 shrink-0" />
            <div>
              <h2 className="font-bold text-paper">Access Denied</h2>
              <p className="text-xs text-muted mt-1">Admin privileges are required to view User Management.</p>
            </div>
          </div>
        </div>
      </AppLayout>
    )
  }

  const activeCount = users.filter((u) => (u.status || 'active') === 'active').length
  const inactiveCount = users.filter((u) => u.status === 'inactive').length

  return (
    <AppLayout title="User Management">
      <div className="space-y-5">
        {/* Header & Stats Banner */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="font-disp text-lg tracking-wide uppercase text-paper">User Administration</h2>
            <p className="text-xs text-muted">Manage system users, access roles, account lifecycle, and audit activity</p>
          </div>
          {users.length > 0 && (
            <div className="flex items-center gap-3 text-xs">
              <span className="px-3 py-1.5 rounded-lg bg-panel border border-border text-paper">
                Total: <strong className="text-sage">{users.length}</strong>
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-panel border border-border text-paper">
                Active: <strong className="text-sage">{activeCount}</strong>
              </span>
              {inactiveCount > 0 && (
                <span className="px-3 py-1.5 rounded-lg bg-panel border border-toad/30 text-toad">
                  Inactive: <strong>{inactiveCount}</strong>
                </span>
              )}
            </div>
          )}
        </div>

        {/* Feedback Alert */}
        {feedback && (
          <div
            className={`p-4 rounded-lg text-xs flex items-center justify-between border ${
              feedback.type === 'success'
                ? 'bg-sage/10 border-sage/30 text-sage'
                : 'bg-toad/10 border-toad/30 text-toad'
            }`}
          >
            <div className="flex items-center gap-2">
              {feedback.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 shrink-0" />
              )}
              <span>{feedback.text}</span>
            </div>
            <button onClick={() => setFeedback(null)} className="hover:opacity-75">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Table / Loading / Error */}
        {loading ? (
          <Loading label="Loading users…" />
        ) : error ? (
          <ErrorMessage message={error} onRetry={load} />
        ) : users.length === 0 ? (
          <EmptyState title="No users found" hint="No user accounts are currently registered in the system." />
        ) : (
          <div className="nx-card overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase tracking-[0.15em] text-muted border-b border-border">
                  <th className="px-5 py-3 font-normal">Username</th>
                  <th className="px-5 py-3 font-normal">Email</th>
                  <th className="px-5 py-3 font-normal">Role</th>
                  <th className="px-5 py-3 font-normal">Status</th>
                  <th className="px-5 py-3 font-normal">Created At</th>
                  <th className="px-5 py-3 font-normal text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  const isSelf = currentUserId === u.id || currentUser?.username === u.username
                  const isAct = (u.status || 'active') === 'active'

                  return (
                    <tr
                      key={u.id ?? u.username}
                      className="border-b border-border/60 last:border-0 hover:bg-white/[0.03] transition-colors"
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-paper">{u.username}</span>
                          {isSelf && (
                            <span className="text-[10px] tracking-wider uppercase px-1.5 py-0.5 rounded bg-volt/10 border border-volt/25 text-volt">
                              You
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-3 text-muted">{u.email || '—'}</td>
                      <td className="px-5 py-3">
                        <RoleBadge role={u.role} />
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge status={u.status} />
                      </td>
                      <td className="px-5 py-3 text-muted">{formatDate(u.created_at)}</td>
                      <td className="px-5 py-3 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          {/* View details */}
                          <button
                            onClick={() => handleOpenDetails(u)}
                            title="View details & activity"
                            className="px-2.5 py-1 text-xs rounded border border-border hover:border-paper/40 text-paper/80 hover:text-paper transition-colors flex items-center gap-1"
                          >
                            <Eye className="w-3 h-3" />
                            <span>View</span>
                          </button>

                          {/* Change role */}
                          <button
                            onClick={() => handleOpenRoleModal(u)}
                            title="Change user role"
                            className="px-2.5 py-1 text-xs rounded border border-border hover:border-volt/50 text-paper/80 hover:text-volt transition-colors flex items-center gap-1"
                          >
                            <Shield className="w-3 h-3" />
                            <span>Role</span>
                          </button>

                          {/* Activate / Deactivate */}
                          {isAct ? (
                            <button
                              onClick={() => handleOpenStatusModal(u)}
                              title="Deactivate user"
                              className="px-2.5 py-1 text-xs rounded border border-toad/30 hover:bg-toad/10 text-toad transition-colors flex items-center gap-1"
                            >
                              <UserX className="w-3 h-3" />
                              <span>Deactivate</span>
                            </button>
                          ) : (
                            <button
                              onClick={() => handleOpenStatusModal(u)}
                              title="Reactivate user"
                              className="px-2.5 py-1 text-xs rounded border border-sage/30 hover:bg-sage/10 text-sage transition-colors flex items-center gap-1"
                            >
                              <UserCheck className="w-3 h-3" />
                              <span>Activate</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* VIEW DETAILS & ACTIVITY MODAL */}
        {/* ------------------------------------------------------------------ */}
        {viewingUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <div className="nx-card w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden animate-fadeIn">
              {/* Modal Header */}
              <div className="px-6 py-4 border-b border-border flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full bg-sage/15 flex items-center justify-center">
                    <User className="w-4 h-4 text-sage" />
                  </div>
                  <div>
                    <h3 className="font-disp text-base text-paper uppercase tracking-wider">
                      User Profile & Activity
                    </h3>
                    <p className="text-xs text-muted">{viewingUser.username}</p>
                  </div>
                </div>
                <button
                  onClick={() => setViewingUser(null)}
                  className="text-muted hover:text-paper p-1 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-6 overflow-y-auto space-y-6 flex-1">
                {detailsLoading ? (
                  <Loading label="Fetching user activity & ownership…" />
                ) : (
                  <>
                    {/* User Overview Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 rounded-lg bg-ink/50 border border-border">
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-muted block">Username</span>
                        <span className="font-bold text-sm text-paper">{detailsData?.user?.username}</span>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-muted block">Email</span>
                        <span className="text-xs text-paper/90 break-all">{detailsData?.user?.email || '—'}</span>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-muted block">Role</span>
                        <div className="mt-0.5">
                          <RoleBadge role={detailsData?.user?.role} />
                        </div>
                      </div>
                      <div>
                        <span className="text-[10px] uppercase tracking-wider text-muted block">Status</span>
                        <div className="mt-0.5">
                          <StatusBadge status={detailsData?.user?.status} />
                        </div>
                      </div>
                    </div>

                    {/* Historical ownership notice */}
                    <div className="p-3 rounded-lg bg-panel border border-border text-xs text-muted flex items-start gap-2">
                      <Clock className="w-4 h-4 text-volt shrink-0 mt-0.5" />
                      <div>
                        <span className="font-medium text-paper/90">Data Ownership Note:</span>
                        <p className="mt-0.5">
                          {detailsData?.ownership_note ||
                            'Historical datasets and pipelines uploaded before user tracking have unassigned ownership. New dataset uploads are tracked in real time.'}
                        </p>
                      </div>
                    </div>

                    {/* Datasets Uploaded */}
                    <div>
                      <div className="flex items-center gap-2 mb-2.5">
                        <Database className="w-4 h-4 text-sage" />
                        <h4 className="font-disp text-sm uppercase tracking-wider text-paper">
                          Uploaded Datasets ({detailsData?.datasets?.length || 0})
                        </h4>
                      </div>
                      {detailsData?.datasets?.length > 0 ? (
                        <div className="border border-border rounded-lg overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="text-left text-[10px] uppercase tracking-wider text-muted bg-panel/60 border-b border-border">
                                <th className="px-4 py-2">ID</th>
                                <th className="px-4 py-2">Filename</th>
                                <th className="px-4 py-2">Version</th>
                                <th className="px-4 py-2">Uploaded</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detailsData.datasets.map((d) => (
                                <tr key={d.id} className="border-b border-border/40 last:border-0 hover:bg-white/[0.02]">
                                  <td className="px-4 py-2 font-bold text-paper">#{d.id}</td>
                                  <td className="px-4 py-2 text-paper/90">{d.file_name}</td>
                                  <td className="px-4 py-2 text-muted">v{d.version}</td>
                                  <td className="px-4 py-2 text-muted">{formatDate(d.uploaded_at)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-xs text-muted italic bg-panel/30 p-3 rounded border border-border/50">
                          No datasets currently linked to this user.
                        </p>
                      )}
                    </div>

                    {/* Pipelines Executed */}
                    <div>
                      <div className="flex items-center gap-2 mb-2.5">
                        <Workflow className="w-4 h-4 text-volt" />
                        <h4 className="font-disp text-sm uppercase tracking-wider text-paper">
                          Executed Pipelines ({detailsData?.pipelines?.length || 0})
                        </h4>
                      </div>
                      {detailsData?.pipelines?.length > 0 ? (
                        <div className="border border-border rounded-lg overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="text-left text-[10px] uppercase tracking-wider text-muted bg-panel/60 border-b border-border">
                                <th className="px-4 py-2">Pipeline ID</th>
                                <th className="px-4 py-2">Dataset ID</th>
                                <th className="px-4 py-2">Status</th>
                                <th className="px-4 py-2">Started</th>
                                <th className="px-4 py-2 text-right">Clean Rows</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detailsData.pipelines.map((p) => (
                                <tr key={p.id} className="border-b border-border/40 last:border-0 hover:bg-white/[0.02]">
                                  <td className="px-4 py-2 font-bold text-paper">#{p.id}</td>
                                  <td className="px-4 py-2 text-muted">dataset #{p.dataset_id}</td>
                                  <td className="px-4 py-2">
                                    <span className="nx-badge border border-border text-[10px]">
                                      {p.status || 'UNKNOWN'}
                                    </span>
                                  </td>
                                  <td className="px-4 py-2 text-muted">{formatDate(p.started_at)}</td>
                                  <td className="px-4 py-2 text-right text-sage">{p.clean_rows ?? '—'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      ) : (
                        <p className="text-xs text-muted italic bg-panel/30 p-3 rounded border border-border/50">
                          No pipelines currently linked to this user.
                        </p>
                      )}
                    </div>

                    {/* Recent Activity Log */}
                    <div>
                      <div className="flex items-center gap-2 mb-2.5">
                        <Activity className="w-4 h-4 text-toad" />
                        <h4 className="font-disp text-sm uppercase tracking-wider text-paper">Recent Activity</h4>
                      </div>
                      {detailsData?.recent_activity?.length > 0 ? (
                        <div className="space-y-2">
                          {detailsData.recent_activity.map((act) => (
                            <div
                              key={act.id}
                              className="p-3 rounded-lg bg-panel border border-border flex items-center justify-between text-xs"
                            >
                              <div className="flex items-center gap-2.5">
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-volt/15 text-volt border border-volt/25">
                                  {act.activity_type}
                                </span>
                                <span className="text-paper/90">{act.description}</span>
                              </div>
                              <span className="text-[10px] text-muted">{formatDate(act.created_at)}</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-muted italic bg-panel/30 p-3 rounded border border-border/50">
                          No audit activity recorded for this user yet.
                        </p>
                      )}
                    </div>
                  </>
                )}
              </div>

              {/* Modal Footer */}
              <div className="px-6 py-3 border-t border-border flex justify-end">
                <button
                  onClick={() => setViewingUser(null)}
                  className="px-4 py-2 text-xs uppercase tracking-wider rounded border border-border hover:bg-white/[0.05] text-paper transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* CHANGE ROLE MODAL */}
        {/* ------------------------------------------------------------------ */}
        {roleModalUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <div className="nx-card w-full max-w-md p-6 space-y-4 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-volt" />
                  <h3 className="font-disp text-base text-paper uppercase tracking-wider">Change User Role</h3>
                </div>
                <button
                  onClick={() => setRoleModalUser(null)}
                  className="text-muted hover:text-paper transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {currentUserId === roleModalUser.id || currentUser?.username === roleModalUser.username ? (
                <div className="p-4 rounded-lg bg-toad/10 border border-toad/30 text-toad text-xs space-y-2">
                  <div className="flex items-center gap-2 font-bold">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Self-Role Modification Prohibited</span>
                  </div>
                  <p className="text-paper/80">
                    Administrators cannot change their own role. To modify this account's permissions, another
                    administrator must perform the action.
                  </p>
                  <div className="pt-2">
                    <button
                      onClick={() => setRoleModalUser(null)}
                      className="w-full py-2 text-xs uppercase tracking-wider rounded bg-panel border border-border text-paper"
                    >
                      Close
                    </button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmitRole} className="space-y-4">
                  <p className="text-xs text-muted">
                    Select a new authorization role for user{' '}
                    <strong className="text-paper">{roleModalUser.username}</strong>:
                  </p>

                  <div className="space-y-2">
                    {['Admin', 'Data Engineer', 'Viewer'].map((r) => (
                      <label
                        key={r}
                        className={`flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-colors ${
                          selectedRole === r
                            ? 'bg-volt/10 border-volt/50 text-paper'
                            : 'bg-panel/40 border-border text-muted hover:border-paper/40'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="radio"
                            name="roleSelection"
                            value={r}
                            checked={selectedRole === r}
                            onChange={(e) => setSelectedRole(e.target.value)}
                            className="accent-volt"
                          />
                          <span className="text-sm font-medium">{r}</span>
                        </div>
                        <RoleBadge role={r} />
                      </label>
                    ))}
                  </div>

                  <div className="p-3 rounded bg-ink/60 border border-border text-[11px] text-muted space-y-1">
                    <span className="font-bold text-paper block">Role Capabilities:</span>
                    {selectedRole === 'Admin' && <p>• Full administrative access, user management, and system configuration.</p>}
                    {selectedRole === 'Data Engineer' && <p>• Dataset upload, pipeline execution, cleaning rules, and analytics.</p>}
                    {selectedRole === 'Viewer' && <p>• Upload and work with permitted datasets with no administrative privileges.</p>}
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                    <button
                      type="button"
                      onClick={() => setRoleModalUser(null)}
                      className="px-4 py-2 text-xs uppercase tracking-wider rounded border border-border hover:bg-white/[0.05] text-paper transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={submittingRole || selectedRole === roleModalUser.role}
                      className="px-4 py-2 text-xs uppercase tracking-wider rounded bg-volt text-ink font-bold hover:bg-volt/90 disabled:opacity-50 transition-colors"
                    >
                      {submittingRole ? 'Saving…' : 'Confirm Change'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------------ */}
        {/* ACTIVATE / DEACTIVATE MODAL */}
        {/* ------------------------------------------------------------------ */}
        {statusModalUser && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <div className="nx-card w-full max-w-md p-6 space-y-4 animate-fadeIn">
              {(() => {
                const isAct = (statusModalUser.status || 'active') === 'active'
                const isSelf = currentUserId === statusModalUser.id || currentUser?.username === statusModalUser.username

                return (
                  <>
                    <div className="flex items-center justify-between border-b border-border pb-3">
                      <div className="flex items-center gap-2">
                        {isAct ? (
                          <UserX className="w-5 h-5 text-toad" />
                        ) : (
                          <UserCheck className="w-5 h-5 text-sage" />
                        )}
                        <h3 className="font-disp text-base text-paper uppercase tracking-wider">
                          {isAct ? 'Deactivate User' : 'Reactivate User'}
                        </h3>
                      </div>
                      <button
                        onClick={() => setStatusModalUser(null)}
                        className="text-muted hover:text-paper transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    </div>

                    {isAct ? (
                      <div className="space-y-3 text-xs">
                        {isSelf ? (
                          <div className="p-4 rounded-lg bg-toad/15 border border-toad/40 text-toad space-y-2">
                            <div className="flex items-center gap-2 font-bold text-sm">
                              <AlertTriangle className="w-5 h-5 shrink-0" />
                              <span>Deactivating Your Own Admin Account</span>
                            </div>
                            <p className="text-paper/90">
                              Warning: You are attempting to deactivate your currently logged-in Admin account (
                              <strong>{statusModalUser.username}</strong>). If deactivated, you will immediately lose
                              access to all protected NEXUS APIs and dashboards upon next session check.
                            </p>
                            <label className="flex items-start gap-2 pt-2 cursor-pointer text-paper">
                              <input
                                type="checkbox"
                                checked={confirmSelfDeactivate}
                                onChange={(e) => setConfirmSelfDeactivate(e.target.checked)}
                                className="mt-0.5 accent-toad"
                              />
                              <span>I understand the consequences and confirm deactivation of my own account.</span>
                            </label>
                          </div>
                        ) : (
                          <div className="p-3 rounded-lg bg-ink/60 border border-border space-y-2">
                            <p className="text-paper/90">
                              Are you sure you want to deactivate{' '}
                              <strong className="text-paper">{statusModalUser.username}</strong>?
                            </p>
                            <p className="text-muted text-[11px]">
                              Deactivated users are immediately blocked from authenticating and cannot access any
                              protected API endpoints until reactivated.
                            </p>
                          </div>
                        )}

                        <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
                          <button
                            type="button"
                            onClick={() => setStatusModalUser(null)}
                            className="px-4 py-2 text-xs uppercase tracking-wider rounded border border-border hover:bg-white/[0.05] text-paper transition-colors"
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            onClick={handleSubmitStatus}
                            disabled={submittingStatus || (isSelf && !confirmSelfDeactivate)}
                            className="px-4 py-2 text-xs uppercase tracking-wider rounded bg-toad text-white font-bold hover:bg-toad/90 disabled:opacity-50 transition-colors"
                          >
                            {submittingStatus ? 'Processing…' : 'Confirm Deactivation'}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-3 text-xs">
                        <div className="p-3 rounded-lg bg-sage/10 border border-sage/30 text-sage space-y-1">
                          <p className="font-bold">Restore Account Access</p>
                          <p className="text-paper/80">
                            Reactivating <strong className="text-paper">{statusModalUser.username}</strong> will restore
                            their ability to log in and access NEXUS resources matching their assigned role (
                            {statusModalUser.role}).
                          </p>
                        </div>

                        <div className="flex items-center justify-end gap-2 pt-3 border-t border-border">
                          <button
                            type="button"
                            onClick={() => setStatusModalUser(null)}
                            className="px-4 py-2 text-xs uppercase tracking-wider rounded border border-border hover:bg-white/[0.05] text-paper transition-colors"
                          >
                            Cancel
                          </button>
                          <button
                            type="button"
                            onClick={handleSubmitStatus}
                            disabled={submittingStatus}
                            className="px-4 py-2 text-xs uppercase tracking-wider rounded bg-sage text-ink font-bold hover:bg-sage/90 disabled:opacity-50 transition-colors"
                          >
                            {submittingStatus ? 'Activating…' : 'Confirm Reactivation'}
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )
              })()}
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  )
}
