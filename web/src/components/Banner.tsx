import { useState } from 'react'

export default function Banner() {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null
  return (
    <div className="absolute bottom-2 left-1/2 -translate-x-1/2 z-[1000] max-w-xl bg-neutral-900/95 border border-neutral-700 rounded px-4 py-2 text-sm text-neutral-200 shadow-lg">
      <button
        onClick={() => setDismissed(true)}
        className="absolute top-1 right-2 text-neutral-500 hover:text-neutral-200"
        aria-label="Dismiss"
      >
        ×
      </button>
      Every line of dialogue in <em>EarthBound</em>, mapped to where it's spoken —
      including content unreachable in normal play.{' '}
      <a
        href="https://example.substack.com"
        target="_blank"
        rel="noreferrer"
        className="text-amber-300 underline"
      >
        Read the project
      </a>
      .
    </div>
  )
}
