import { useQuery } from '@tanstack/react-query'

const PAIRS = ['EURUSD', 'GBPUSD', 'USDCHF', 'USDCAD', 'AUDUSD', 'USDJPY', 'NZDUSD', 'XAUUSD', 'BTCUSD', 'ETHUSD']

export default function CRTScanner() {
  const { data: approvals = [] } = useQuery({ queryKey: ['approvals'], queryFn: () => fetch('/api/system/approvals').then(r => r.json()), refetchInterval: 5000 })

  const crtSignals = approvals.filter(a => a.source_agent === 'crt_agent')

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">CRT Scanner</h2>
      <div className="grid grid-cols-5 gap-3 mb-6">
        {PAIRS.map(pair => {
          const signal = crtSignals.find(s => s.pair === pair)
          return (
            <div key={pair} className={`rounded-lg p-3 border text-center ${signal ? 'bg-yellow-900/30 border-yellow-600' : 'bg-slate-800 border-slate-700'}`}>
              <div className="text-white font-bold text-sm">{pair}</div>
              <div className={`text-xs mt-1 ${signal ? 'text-yellow-400' : 'text-slate-500'}`}>
                {signal ? `${signal.direction} pending` : 'No signal'}
              </div>
            </div>
          )
        })}
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="text-sm font-bold text-slate-300 mb-3">Active CRT Signals</h3>
        {crtSignals.length === 0 ? (
          <p className="text-slate-500 text-sm">No active CRT signals. Run the scanner to detect setups.</p>
        ) : (
          crtSignals.map(s => (
            <div key={s.signal_id} className="border-b border-slate-700 py-2 flex justify-between text-sm">
              <span className="text-white">{s.pair} <span className={s.direction === 'LONG' ? 'text-green-400' : 'text-red-400'}>{s.direction}</span></span>
              <span className="text-slate-400">Entry: {s.entry_price} | SL: {s.sl} | TP1: {s.tp1}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
