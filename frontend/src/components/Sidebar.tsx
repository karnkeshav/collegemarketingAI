import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Building2,
  Users,
  Send,
  BarChart3,
  GraduationCap,
} from 'lucide-react'

const links = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/colleges', icon: Building2, label: 'Colleges' },
  { to: '/contacts', icon: Users, label: 'Contacts' },
  { to: '/campaigns', icon: Send, label: 'Campaigns' },
  { to: '/reports', icon: BarChart3, label: 'Reports' },
]

export function Sidebar() {
  return (
    <aside className="w-60 min-h-screen bg-slate-900 flex flex-col shrink-0">
      <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-700">
        <GraduationCap size={28} className="text-indigo-400" />
        <div>
          <p className="text-white font-semibold text-sm leading-tight">CollegeMarketing</p>
          <p className="text-slate-400 text-xs">AI Outreach Platform</p>
        </div>
      </div>

      <nav className="flex flex-col gap-1 p-3 flex-1">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-600 text-white'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-700">
        <p className="text-slate-500 text-xs">ready4industry@gmail.com</p>
      </div>
    </aside>
  )
}
