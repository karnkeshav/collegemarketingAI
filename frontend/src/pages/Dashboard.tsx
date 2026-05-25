import { useEffect, useState } from 'react'
import {
  Building2, Users, CheckCircle2, Send, AlertCircle, Mail
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend
} from 'recharts'
import { StatsCard } from '../components/StatsCard'
import { reportsApi, scraperApi } from '../api/client'
import type { OverviewStats } from '../types'

const STATE_COLORS = ['#6366f1', '#06b6d4', '#f59e0b', '#10b981', '#f43f5e']

export function Dashboard() {
  const [stats, setStats] = useState<OverviewStats | null>(null)
  const [scrapeStatus, setScrapeStatus] = useState<Record<string, { status: string; done: number; total: number }>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([reportsApi.overview(), scraperApi.status()])
      .then(([s, sc]) => { setStats(s); setScrapeStatus(sc) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <p className="text-slate-500 text-sm mt-1">College outreach overview across all states</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
        <StatsCard title="Total Colleges" value={stats.total_colleges} icon={Building2} color="indigo" />
        <StatsCard title="Total Contacts" value={stats.total_contacts} icon={Users} color="blue" />
        <StatsCard title="Validated Emails" value={stats.validated_contacts} icon={CheckCircle2} color="green"
          sub={`${stats.invalid_contacts} invalid`} />
        <StatsCard title="Campaigns" value={stats.total_campaigns} icon={Send} color="purple" />
        <StatsCard title="Emails Sent" value={stats.emails_sent} icon={Mail} color="amber" />
        <StatsCard title="Bounced" value={stats.emails_bounced} icon={AlertCircle} color="red" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* State bar chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">Contacts by State</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={stats.by_state}>
              <XAxis dataKey="state" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="contacts" radius={[4, 4, 0, 0]}>
                {stats.by_state.map((_, i) => (
                  <Cell key={i} fill={STATE_COLORS[i % STATE_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Role pie chart */}
        <div className="bg-white rounded-xl border border-slate-200 p-5">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">Contacts by Role</h2>
          {stats.by_role.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={stats.by_role}
                  dataKey="count"
                  nameKey="role"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={({ role, percent }) => `${role} ${(percent * 100).toFixed(0)}%`}
                >
                  {stats.by_role.map((_, i) => (
                    <Cell key={i} fill={STATE_COLORS[i % STATE_COLORS.length]} />
                  ))}
                </Pie>
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm">
              No contacts yet — start scraping to populate data
            </div>
          )}
        </div>
      </div>

      {/* Active scrape status */}
      {Object.entries(scrapeStatus).some(([, v]) => v.status === 'running') && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-amber-800 mb-2">Scrape in progress</h3>
          {Object.entries(scrapeStatus).filter(([, v]) => v.status === 'running').map(([code, p]) => (
            <div key={code} className="mb-2">
              <div className="flex justify-between text-xs text-amber-700 mb-1">
                <span>{code}</span>
                <span>{p.done}/{p.total}</span>
              </div>
              <div className="w-full bg-amber-200 rounded-full h-2">
                <div
                  className="bg-amber-500 h-2 rounded-full transition-all"
                  style={{ width: p.total ? `${(p.done / p.total) * 100}%` : '5%' }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
