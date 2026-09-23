import { useQuery } from '@tanstack/react-query'

const STATUS_COLORS = {
  IDEA_PROPOSED: 'bg-slate-600', BACKTESTING: 'bg-blue-600', RISK_REVIEW: 'bg-yellow-600',
  PAPER_TRADING: 'bg-purple-600', LIVE_TRADING: 'bg-green-600', PAUSED: 'bg-orange-600', RETIRED: 'bg-slate-700',
}

export default function Strategies() {
  const { data: strategies = [] } = useQuery({ queryKey: ['strategies'], queryFn: () => fetch('/api/strategies/').then(r => r.json()) })
  const { data: ideas = [] } = useQuery({ queryKey: ['ideas'], queryFn: () => fetch('/api/strategies/ideas').then(r => r.json()) })

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Strategy Manager</h2>
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700">
          <th className="text-left py-2">Name</th><th className="text-left">Status</th><th className="text-left">Asset</th><th className="text-left">Frequency</th>
        </tr></thead>
        <tbody>
          {strategies.map(s => (
            <tr key={s.id} className="border-b border-slate-800 hover:bg-slate-800">
              <td className="py-2 text-white">{s.name}</td>
              <td><span className={`px-2 py-0.5 rounded text-xs text-white ${STATUS_COLORS[s.status] || 'bg-slate-600'}`}>{s.status}</span></td>
              <td className="text-slate-400">{s.asset_class || '-'}</td>
              <td className="text-slate-400">{s.frequency || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3 className="text-lg font-bold mt-8 mb-3">Research Ideas ({ideas.length})</h3>
      <div className="space-y-2">
        {ideas.slice(0, 10).map(i => (
          <div key={i.id} className="bg-slate-800 border border-slate-700 rounded p-3 flex justify-between">
            <div>
              <span className="text-white text-sm">{i.title?.slice(0, 60)}</span>
              <span className={`ml-2 text-xs px-2 py-0.5 rounded ${i.status === 'APPROVED' ? 'bg-green-800 text-green-300' : 'bg-slate-700 text-slate-400'}`}>{i.status}</span>
            </div>
            <span className="text-slate-400 text-sm">Score: {i.total_score || '-'}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
