import { BarChart2, PhoneCall } from 'lucide-react'
import { NavLink } from 'react-router-dom'

export default function Navbar() {
  const link = 'flex items-center gap-1.5 text-sm transition-colors'
  const active = 'text-white'
  const inactive = 'text-gray-400 hover:text-white'

  return (
    <nav className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-6">
      <div className="flex items-center gap-2 text-white font-semibold mr-4">
        <PhoneCall size={18} className="text-blue-400" />
        <span>Support Dashboard</span>
      </div>

      <NavLink to="/dashboard" className={({ isActive }) => `${link} ${isActive ? active : inactive}`}>
        <BarChart2 size={15} />
        Dashboard
      </NavLink>

      <NavLink to="/transcripts" className={({ isActive }) => `${link} ${isActive ? active : inactive}`}>
        <PhoneCall size={15} />
        Transcript Analytics
      </NavLink>
    </nav>
  )
}
