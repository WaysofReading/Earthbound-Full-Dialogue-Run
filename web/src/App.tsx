import { useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import { useStore } from './lib/store'
import MapView from './views/MapView'
import ArchiveView from './views/ArchiveView'
import SearchView from './views/SearchView'
import SmokeTest from './views/SmokeTest'

function NavBar() {
  const counts = useStore((s) => s.manifest?.counts)
  const linkCls = ({ isActive }: { isActive: boolean }) =>
    `px-3 py-1.5 rounded text-sm font-medium ${
      isActive ? 'bg-neutral-700 text-white' : 'text-neutral-300 hover:bg-neutral-800'
    }`
  return (
    <header className="flex items-center gap-2 px-3 py-2 bg-neutral-950 border-b border-neutral-800 shrink-0">
      <span className="font-semibold text-sm mr-2 text-amber-300">
        EarthBound · Full Dialogue
      </span>
      <NavLink to="/" className={linkCls} end>
        Map
      </NavLink>
      <NavLink to="/archive" className={linkCls}>
        Archive
      </NavLink>
      <NavLink to="/search" className={linkCls}>
        Search
      </NavLink>
      {counts && (
        <span className="ml-auto text-xs text-neutral-500 font-mono">
          {counts.total} entities · {counts.npc} npcs
        </span>
      )}
    </header>
  )
}

export default function App() {
  const loadStartup = useStore((s) => s.loadStartup)
  const manifest = useStore((s) => s.manifest)
  const error = useStore((s) => s.error)
  const location = useLocation()

  useEffect(() => {
    loadStartup()
  }, [loadStartup])

  // The smoke test renders standalone (it is the coordinate regression page).
  const isSmoke = location.pathname === '/smoke'

  if (error) {
    return (
      <div className="p-6 text-red-400">
        <h1 className="font-bold mb-2">Failed to load data</h1>
        <pre className="text-sm whitespace-pre-wrap">{error}</pre>
        <p className="mt-3 text-neutral-400 text-sm">
          Run <code>python data-prep/prep.py</code> to generate web/public, then reload.
        </p>
      </div>
    )
  }

  if (!manifest) {
    return (
      <div className="h-full flex items-center justify-center text-neutral-400">
        Loading dialogue archive…
      </div>
    )
  }

  if (isSmoke) {
    return (
      <Routes>
        <Route path="/smoke" element={<SmokeTest />} />
      </Routes>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <NavBar />
      <main className="flex-1 min-h-0 relative">
        <Routes>
          <Route path="/" element={<MapView />} />
          <Route path="/map" element={<MapView />} />
          <Route path="/entity/:id" element={<MapView />} />
          <Route path="/archive" element={<ArchiveView />} />
          <Route path="/node/:id" element={<ArchiveView />} />
          <Route path="/search" element={<SearchView />} />
          <Route path="*" element={<MapView />} />
        </Routes>
      </main>
    </div>
  )
}
