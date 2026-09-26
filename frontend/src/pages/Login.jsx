import React, { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { LogIn, Eye, EyeOff, Loader2 } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/dashboard'

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await signIn(username, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err?.message || 'Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-full bg-ink relative overflow-hidden flex items-center justify-center px-4">
      {/* ambient NEXUS backdrop, echoing the hero without reusing its assets */}
      <div className="absolute inset-0 opacity-40" style={{
        background: 'radial-gradient(ellipse at 30% 20%, rgba(255,122,47,0.12), transparent 55%), radial-gradient(ellipse at 80% 80%, rgba(159,232,255,0.10), transparent 55%)'
      }} />
      <div className="absolute inset-0 pointer-events-none opacity-[0.05]" style={{
        backgroundImage: 'linear-gradient(rgba(239,232,218,.3) 1px, transparent 1px), linear-gradient(90deg, rgba(239,232,218,.3) 1px, transparent 1px)',
        backgroundSize: '42px 42px'
      }} />

      <div className="relative z-10 w-full max-w-sm">
        <div className="flex items-center justify-center gap-2 mb-8">
          <span className="w-2 h-2 rounded-full bg-sage shadow-glow" />
          <span className="font-disp text-3xl tracking-[0.15em]">NEXUS</span>
        </div>

        <div className="nx-card p-7 shadow-glow">
          <p className="text-[10px] tracking-[0.3em] uppercase text-volt mb-1">Access Terminal</p>
          <h2 className="font-disp text-2xl mb-6">Sign in</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[10px] tracking-[0.2em] uppercase text-muted mb-1.5">Username</label>
              <input
                required
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-black/30 border border-border rounded-lg px-3.5 py-2.5 text-sm text-paper
                  focus:outline-none focus:border-sage/60 focus:ring-1 focus:ring-sage/30 transition-colors"
                placeholder="your.username"
              />
            </div>

            <div>
              <label className="block text-[10px] tracking-[0.2em] uppercase text-muted mb-1.5">Password</label>
              <div className="relative">
                <input
                  required
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-black/30 border border-border rounded-lg px-3.5 py-2.5 pr-10 text-sm text-paper
                    focus:outline-none focus:border-sage/60 focus:ring-1 focus:ring-sage/30 transition-colors"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((s) => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-paper"
                  tabIndex={-1}
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="text-xs text-toad bg-toad/10 border border-toad/30 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-sage text-ink font-bold text-sm
                tracking-widest uppercase py-3 rounded-lg hover:brightness-110 active:scale-[0.99]
                disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-glow"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogIn className="w-4 h-4" />}
              {loading ? 'Authenticating…' : 'Enter Terminal'}
            </button>
          </form>

          <div className="mt-5 text-center">
            <p className="text-xs text-muted">
              Don't have an account?{' '}
              <Link to="/register" className="text-sage hover:underline font-semibold">
                Create Account
              </Link>
            </p>
          </div>
        </div>

        <p className="text-center text-[11px] text-muted mt-6">
          <Link to="/" className="hover:text-sage transition-colors">← Back to Hidden Leaf</Link>
        </p>
      </div>
    </div>
  )
}
