import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Navbar from './components/shared/Navbar'
import DashboardPage from './pages/DashboardPage'
import TranscriptPage from './pages/TranscriptPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-white">
        <Navbar />
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/transcripts" element={<TranscriptPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
