import { useQuery } from '@tanstack/react-query'

export default function RiskControls() {
  const { data: limits } = useQuery({ queryKey: ['limits'], queryFn: () => fetch('/api/risk/limits').then(r => r.json()) })

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Risk Controls</h2>
      {limits && (
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(limits).map(([key, val]) => (
            <div key={key} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
              <div className="text-slate-400 text-xs uppercase">{key.replace(/_/g, ' ')}</div>
              <div className="text-2xl font-bold text-white mt-1">
                {typeof val === 'number' ? (val < 1 ? `${(val * 100).toFixed(0)}%` : val) : String(val)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
