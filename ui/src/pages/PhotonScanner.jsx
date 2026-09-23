import { useQuery } from '@tanstack/react-query'

export default function PhotonScanner() {
  const { data: expectations = [] } = useQuery({ queryKey: ['expectations'], queryFn: () => fetch('/api/photon/expectations').then(r => r.json()), refetchInterval: 10000 })

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Photon Scanner</h2>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-bold text-slate-300 mb-3">Expectation Board</h3>
        {expectations.length === 0 ? (
          <p className="text-slate-500 text-sm">No active expectations. Run the Photon scanner to create anticipatory zones.</p>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="text-slate-400 border-b border-slate-700">
              <th className="text-left py-1">Pair</th><th className="text-left">Direction</th><th className="text-left">Zone</th><th className="text-left">Status</th><th className="text-left">Created</th>
            </tr></thead>
            <tbody>
              {expectations.map(e => (
                <tr key={e.id} className="border-b border-slate-800">
                  <td className="py-1.5 text-white">{e.pair}</td>
                  <td className={e.direction === 'LONG' ? 'text-green-400' : 'text-red-400'}>{e.direction}</td>
                  <td className="text-slate-300">{e.zone?.[0]?.toFixed(5)} - {e.zone?.[1]?.toFixed(5)}</td>
                  <td><span className={`px-2 py-0.5 rounded text-xs ${e.status === 'PRICE_ARRIVED' ? 'bg-yellow-800 text-yellow-300' : 'bg-slate-700 text-slate-400'}`}>{e.status}</span></td>
                  <td className="text-slate-500">{e.created_at?.slice(0, 16)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
