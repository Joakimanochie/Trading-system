import { useQuery } from '@tanstack/react-query'

const Card = ({ label, value, color = 'text-white' }) => (
  <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
    <div className="text-slate-400 text-xs uppercase">{label}</div>
    <div className={`text-2xl font-bold mt-1 ${color}`}>{value}</div>
  </div>
)

export default function Dashboard() {
  const { data: risk } = useQuery({ queryKey: ['risk'], queryFn: () => fetch('/api/risk/state').then(r => r.json()), refetchInterval: 30000 })
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: () => fetch('/api/system/health').then(r => r.json()), refetchInterval: 15000 })
  const { data: approvals } = useQuery({ queryKey: ['approvals'], queryFn: () => fetch('/api/system/approvals').then(r => r.json()), refetchInterval: 10000 })

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Dashboard</h2>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card label="Max Drawdown" value={risk ? `${(risk.max_drawdown_pct * 100).toFixed(0)}%` : '...'} />
        <Card label="Daily Loss Limit" value={risk ? `${(risk.daily_loss_limit_pct * 100).toFixed(0)}%` : '...'} />
        <Card label="Max Leverage" value={risk ? `${risk.max_leverage}x` : '...'} />
        <Card label="Pending Signals" value={approvals ? approvals.length : 0} color={approvals?.length > 0 ? 'text-yellow-400' : 'text-green-400'} />
      </div>
      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 mb-4">
        <h3 className="text-sm font-bold text-slate-300 mb-2">System Health</h3>
        {health ? (
          <div className="flex gap-4 flex-wrap">
            <span className={`text-sm ${health.redis ? 'text-green-400' : 'text-red-400'}`}>Redis: {health.redis ? 'OK' : 'DOWN'}</span>
            <span className={`text-sm ${health.db ? 'text-green-400' : 'text-red-400'}`}>DB: {health.db ? 'OK' : 'DOWN'}</span>
            <span className={`text-sm ${health.mt5 ? 'text-green-400' : 'text-red-400'}`}>MT5: {health.mt5 ? 'OK' : 'DOWN'}</span>
            {health.agents?.map(a => (
              <span key={a.name} className={`text-sm ${a.healthy ? 'text-green-400' : 'text-slate-500'}`}>{a.name}: {a.healthy ? 'OK' : 'idle'}</span>
            ))}
          </div>
        ) : <span className="text-slate-500 text-sm">Loading...</span>}
      </div>
    </div>
  )
}
