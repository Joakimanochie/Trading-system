import { Link, useLocation } from 'react-router-dom'

const NAV = [
  { path: '/', label: 'Dashboard', icon: '📊' },
  { path: '/signals', label: 'Signals', icon: '📡' },
  { path: '/strategies', label: 'Strategies', icon: '🎯' },
  { path: '/risk', label: 'Risk', icon: '🛡️' },
  { path: '/performance', label: 'Performance', icon: '📈' },
  { path: '/logs', label: 'System', icon: '🔧' },
  { path: '/crt', label: 'CRT Scanner', icon: '🕯️' },
  { path: '/photon', label: 'Photon', icon: '⚡' },
]

export default function Layout({ children }) {
  const loc = useLocation()
  return (
    <div className="min-h-screen flex">
      <nav className="w-56 bg-slate-900 border-r border-slate-700 p-4 flex flex-col gap-1">
        <h1 className="text-lg font-bold text-white mb-4">Quant OS</h1>
        {NAV.map(n => (
          <Link key={n.path} to={n.path}
            className={`px-3 py-2 rounded text-sm flex items-center gap-2 ${loc.pathname === n.path ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800'}`}>
            <span>{n.icon}</span>{n.label}
          </Link>
        ))}
        <div className="mt-auto pt-4">
          <button onClick={() => { if (confirm('ACTIVATE KILL SWITCH?')) fetch('/api/system/kill?confirm=CONFIRM_KILL', { method: 'POST' }) }}
            className="w-full py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm font-bold">
            KILL SWITCH
          </button>
        </div>
      </nav>
      <main className="flex-1 p-6 overflow-auto">{children}</main>
    </div>
  )
}
