import { useQuery } from '@tanstack/react-query'

export default function SystemLogs() {
  const { data: logs = [] } = useQuery({ queryKey: ['audit'], queryFn: () => fetch('/api/system/audit?limit=50').then(r => r.json()), refetchInterval: 10000 })

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">System Logs & Health</h2>
      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
        <table className="w-full text-xs">
          <thead><tr className="text-slate-400 bg-slate-900">
            <th className="text-left p-2">Time</th><th className="text-left">Actor</th><th className="text-left">Action</th><th className="text-left">Outcome</th>
          </tr></thead>
          <tbody>
            {logs.map(l => (
              <tr key={l.id} className="border-t border-slate-800 hover:bg-slate-750">
                <td className="p-2 text-slate-500">{l.timestamp?.slice(11, 19)}</td>
                <td className="text-slate-300">{l.actor}</td>
                <td className="text-white">{l.action}</td>
                <td className={l.outcome === 'rejected' ? 'text-red-400' : l.outcome === 'approved' ? 'text-green-400' : 'text-slate-400'}>{l.outcome || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
