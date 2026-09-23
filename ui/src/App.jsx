import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Signals from './pages/Signals'
import Strategies from './pages/Strategies'
import RiskControls from './pages/RiskControls'
import Performance from './pages/Performance'
import SystemLogs from './pages/SystemLogs'
import CRTScanner from './pages/CRTScanner'
import PhotonScanner from './pages/PhotonScanner'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 10000 } },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/signals" element={<Signals />} />
            <Route path="/strategies" element={<Strategies />} />
            <Route path="/risk" element={<RiskControls />} />
            <Route path="/performance" element={<Performance />} />
            <Route path="/logs" element={<SystemLogs />} />
            <Route path="/crt" element={<CRTScanner />} />
            <Route path="/photon" element={<PhotonScanner />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
