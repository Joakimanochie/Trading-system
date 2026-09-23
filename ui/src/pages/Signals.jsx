import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export default function Signals() {
  const qc = useQueryClient()
  const { data: approvals = [] } = useQuery({ queryKey: ['approvals'], queryFn: () => fetch('/api/system/approvals').then(r => r.json()), refetchInterval: 5000 })

  const approveMut = useMutation({
    mutationFn: (id) => fetch(`/api/system/approvals/${id}/approve`, { method: 'POST' }).then(r => r.json()),
    onSuccess: () => qc.invalidateQueries(['approvals']),
  })
  const rejectMut = useMutation({
    mutationFn: (id) => fetch(`/api/system/approvals/${id}/reject`, { method: 'POST' }).then(r => r.json()),
    onSuccess: () => qc.invalidateQueries(['approvals']),
  })

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Signal Review</h2>
      {approvals.length === 0 ? (
        <p className="text-slate-500">No pending signals</p>
      ) : (
        <div className="space-y-3">
          {approvals.map(s => (
            <div key={s.signal_id} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span className={`text-sm font-bold ${s.direction === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>{s.direction}</span>
                  <span className="text-white font-bold ml-2">{s.pair}</span>
                  <span className="text-slate-400 text-sm ml-2">via {s.source_agent}</span>
                </div>
                <span className="text-xs text-slate-500">Expires: {new Date(s.expires_at).toLocaleTimeString()}</span>
              </div>
              <div className="grid grid-cols-4 gap-2 text-sm mb-3">
                <div><span className="text-slate-400">Entry:</span> <span className="text-white">{s.entry_price}</span></div>
                <div><span className="text-slate-400">SL:</span> <span className="text-red-400">{s.sl}</span></div>
                <div><span className="text-slate-400">TP1:</span> <span className="text-green-400">{s.tp1}</span></div>
                <div><span className="text-slate-400">Size:</span> <span className="text-white">${Number(s.position_size).toLocaleString()}</span></div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => approveMut.mutate(s.signal_id)} className="px-4 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded text-sm">Approve</button>
                <button onClick={() => rejectMut.mutate(s.signal_id)} className="px-4 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded text-sm">Reject</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
