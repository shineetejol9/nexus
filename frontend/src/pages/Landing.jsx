import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'

// The original hero page (public/landing.html) is loaded verbatim in an iframe so its
// own scoped CSS/JS (GSAP timelines, canvas effects, scroll-triggers) run exactly as
// authored, with zero risk of colliding with the React app's styles or router.
// We only ADD a floating CTA on top — we never touch the hero's own markup/scripts.
export default function Landing() {
  const navigate = useNavigate()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    function onMsg(e) {
      if (e?.data?.type === 'nexus:hero-ready') setReady(true)
    }
    window.addEventListener('message', onMsg)
    // Fallback: reveal the CTA even if the message never arrives (older/blocked browsers)
    const t = setTimeout(() => setReady(true), 4500)
    return () => { window.removeEventListener('message', onMsg); clearTimeout(t) }
  }, [])

  return (
    <div className="relative w-full h-screen overflow-hidden bg-ink">
      <iframe
        title="NEXUS — Naruto Landing"
        src="/landing.html"
        className="w-full h-full border-0"
      />
      <button
        onClick={() => navigate('/login')}
        className={`fixed z-[1000] right-6 bottom-6 flex items-center gap-2 px-6 py-3 rounded-full
          bg-gradient-to-r from-[#e8501e] to-[#ffc23d] text-ink font-bold text-sm tracking-widest uppercase
          shadow-[0_0_30px_rgba(255,122,47,0.45)] transition-all duration-500
          hover:scale-105 active:scale-95
          ${ready ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4 pointer-events-none'}`}
      >
        Enter NEXUS <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  )
}
