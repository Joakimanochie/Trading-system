import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function Performance() {
  const { data: records = [] } = useQuery({ queryKey: ['performance'], queryFn: () => fetch('/api/performance/').then(r => r.json()) })

  const latestWithCurve = records.find(r => r.equity_curve?.length > 0)
  const chartData = latestWithCurve?.equity_curve?.map((v, i) => ({ bar: i, equity: v })) || []

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">Performance Analytics</h2>
      {chartData.length > 0 && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
          <h3 className="text-sm text-slate-400 mb-2">Equity Curve</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="bar" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #475569' }} />
              <Line type="monotone" dataKey="equity" stroke="#22c55e" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <table className="w-full text-sm">
        <thead><tr className="text-slate-400 border-b border-slate-700">
          <th className="text-left py-2">Period</th><th>Sharpe</th><th>CAGR</th><th>Max DD</th><th>Win Rate</th><th>Trades</th>
        </tr></thead>
        <tbody>
          {records.slice(0, 20).map(r => (
            <tr key={r.id} className="border-b border-slate-800 text-center">
              <td className="text-left py-1.5 text-white">{r.period_start?.slice(0, 10)}</td>
              <td>{r.sharpe_ratio?.toFixed(2) || '-'}</td>
              <td>{r.cagr ? `${(r.cagr * 100).toFixed(1)}%` : '-'}</td>
              <td className="text-red-400">{r.max_drawdown_pct ? `${(r.max_drawdown_pct * 100).toFixed(1)}%` : '-'}</td>
              <td>{r.win_rate ? `${(r.win_rate * 100).toFixed(0)}%` : '-'}</td>
              <td>{r.total_trades || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
