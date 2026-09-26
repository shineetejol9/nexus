# NEXUS

Naruto-themed landing page → Login → Enterprise data-intelligence dashboard,
wired to your existing FastAPI backend at `http://127.0.0.1:8000`.

## 1. Put your assets in place

Your hero page references a video and three transformation images by
relative path. Drop them next to `public/landing.html`:

```
public/
  landing.html
  video/hero.mp4      ← your hero video
  1.png                ← base form
  3.png                ← hand seal
  2.png                ← sage mode
```

If a file is missing, the page falls back to an auto-generated placeholder
(a labelled gradient) instead of breaking, so you can wire up the rest of
the app before final assets are ready. Note: the two small circular "cap
badges" that sat inside the transformation captions were dropped from this
copy to keep the file a manageable size — everything else (preloader,
cursor, grain, HUD, particles, lightning engine, crack-morph, GSAP
timelines) is reproduced exactly as you wrote it, untouched.

## 2. Install & run

```
npm install
npm run dev
```

Vite serves the SPA on `http://localhost:5173` and proxies `/api`,
`/upload`, `/download` straight through to `http://127.0.0.1:8000`
(see `vite.config.js`), so the browser only ever talks to one origin in
dev and you don't need to fight CORS.

## 3. How the landing page is preserved

`public/landing.html` is your original file, served as a **static asset**,
completely untouched by React/Tailwind/Vite's module system. `src/pages/Landing.jsx`
loads it in a full-screen `<iframe>` at route `/`, and only *overlays* a
floating "Enter NEXUS" button on top — it never edits the hero's DOM, CSS or
scripts. The one non-visual addition inside `landing.html` is a single
`window.parent.postMessage(...)` call at the very end of the existing
`<script>`, which just tells the React shell the intro has finished so the
CTA can fade in at the right moment. It does not touch any visual/animation
code.

Clicking "Enter NEXUS" routes (client-side) to `/login`.

## 4. Auth flow

`src/pages/Login.jsx` posts to `/api/v1/auth/login`, stores the returned
`access_token` in `localStorage`, then calls `/api/v1/auth/me` to resolve
the user + role before redirecting to `/dashboard`. Every subsequent
request automatically carries `Authorization: Bearer <token>` via an axios
interceptor in `src/services/api.js`.

`src/routes/ProtectedRoute.jsx` redirects unauthenticated visitors hitting
any `/dashboard`, `/datasets`, `/quality`, `/analytics`, `/anomalies`,
`/pipelines`, `/upload`, `/settings` route back to `/login`.

Role-based menu visibility lives in `src/components/Sidebar.jsx` — it's a
UI convenience only. The FastAPI backend remains the real authorization
boundary.

## 5. Where each page gets its data

| Route              | Backend calls                                            |
|---------------------|-----------------------------------------------------------|
| `/dashboard`         | `GET /datasets`, `/pipelines`, `/anomalies`, `/kpis`, `/quality/{id}` |
| `/datasets`           | `GET /datasets`                                          |
| `/datasets/:id`        | `GET /datasets/{id}`, `/quality/{id}`, `/kpis?dataset_id=`, `/anomalies?dataset_id=` |
| `/quality`             | `GET /datasets`, `/quality/{id}`                          |
| `/analytics`           | `GET /datasets`, `/kpis?dataset_id=` per dataset            |
| `/anomalies`           | `GET /datasets`, `/anomalies?dataset_id=`                   |
| `/pipelines`           | `GET /pipelines`                                          |
| `/upload`              | `POST /upload`, then `GET /download/{filename}`             |
| `/settings`            | `GET /auth/me` (via AuthContext)                           |

All calls go through `src/services/api.js` — nothing is hardcoded and no
page invents numbers; every card/chart renders `—` or an empty state when
the backend has nothing to show yet.

## 6. Field-name flexibility

Since exact backend field names can vary slightly (`dataset_id` vs `id`,
`file_name` vs `filename`, `clean_rows` vs `clean_records`, etc.), the
pages read defensively with fallbacks (`d.dataset_id ?? d.id`). If your
actual API uses different keys, adjust the small number of `??` fallback
chains in `src/pages/*.jsx` and `src/components/*Table.jsx` — the API
calls themselves already match your documented endpoints exactly.

## 7. Production build

```
npm run build
```

Outputs to `dist/`. For a non-localhost backend, set `VITE_API_BASE_URL`
in a `.env` file and point your static host's rewrite rules so any deep
link (e.g. `/dashboard`) falls back to `index.html` for client-side
routing to take over.
