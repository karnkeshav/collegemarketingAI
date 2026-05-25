import { useEffect, useState } from 'react'
import { Search, RefreshCw, ExternalLink, Play } from 'lucide-react'
import { collegesApi, scraperApi, statesApi } from '../api/client'
import { Badge } from '../components/Badge'
import type { College, State } from '../types'

const COLLEGE_TYPES = ['Engineering', 'Medical', 'Pharmacy', 'Management', 'Arts', 'Commerce', 'Law', 'Science']

export function Colleges() {
  const [states, setStates] = useState<State[]>([])
  const [colleges, setColleges] = useState<College[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [scraping, setScraping] = useState<string | null>(null)
  const [filters, setFilters] = useState({ state_code: '', college_type: '', search: '' })

  useEffect(() => {
    statesApi.list().then(setStates)
  }, [])

  useEffect(() => {
    load()
  }, [filters, page])

  async function load() {
    setLoading(true)
    const params: Record<string, unknown> = { page, limit: 50 }
    if (filters.state_code) params.state_code = filters.state_code
    if (filters.college_type) params.college_type = filters.college_type
    if (filters.search) params.search = filters.search
    const data = await collegesApi.list(params)
    setColleges(data.items)
    setTotal(data.total)
    setLoading(false)
  }

  async function startScrape(stateCode: string) {
    setScraping(stateCode)
    await scraperApi.start(stateCode)
    // Poll until done
    const interval = setInterval(async () => {
      const status = await scraperApi.status()
      if (status[stateCode]?.status === 'done' || status[stateCode]?.status === 'failed') {
        clearInterval(interval)
        setScraping(null)
        load()
      }
    }, 3000)
  }

  const totalPages = Math.ceil(total / 50)

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Colleges</h1>
          <p className="text-slate-500 text-sm">{total.toLocaleString()} colleges found</p>
        </div>
        <div className="flex gap-2">
          {states.map(s => (
            <button
              key={s.code}
              onClick={() => startScrape(s.code)}
              disabled={scraping === s.code}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {scraping === s.code ? (
                <RefreshCw size={13} className="animate-spin" />
              ) : (
                <Play size={13} />
              )}
              Scrape {s.name}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search colleges..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-300"
            value={filters.search}
            onChange={e => setFilters(f => ({ ...f, search: e.target.value }))}
          />
        </div>
        <select
          className="px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-300"
          value={filters.state_code}
          onChange={e => setFilters(f => ({ ...f, state_code: e.target.value }))}
        >
          <option value="">All States</option>
          {states.map(s => <option key={s.code} value={s.code}>{s.name}</option>)}
        </select>
        <select
          className="px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-300"
          value={filters.college_type}
          onChange={e => setFilters(f => ({ ...f, college_type: e.target.value }))}
        >
          <option value="">All Types</option>
          {COLLEGE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center h-48">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600" />
          </div>
        ) : colleges.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-400">
            <p className="font-medium">No colleges found</p>
            <p className="text-sm mt-1">Click "Scrape [State]" above to start collecting data</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">College</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">State / City</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">Type</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">Contacts</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">Status</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">Website</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {colleges.map(c => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-800 max-w-xs truncate">{c.name}</td>
                    <td className="px-4 py-3 text-slate-600">
                      <p>{c.state_name}</p>
                      <p className="text-xs text-slate-400">{c.city}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{c.college_type || '—'}</td>
                    <td className="px-4 py-3">
                      <span className="font-semibold text-indigo-600">{c.contact_count}</span>
                    </td>
                    <td className="px-4 py-3"><Badge status={c.scrape_status} /></td>
                    <td className="px-4 py-3">
                      {c.website ? (
                        <a href={c.website} target="_blank" rel="noopener noreferrer"
                          className="text-indigo-500 hover:text-indigo-700 flex items-center gap-1">
                          <ExternalLink size={13} />
                        </a>
                      ) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
            className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40">Previous</button>
          <span className="text-sm text-slate-600">Page {page} of {totalPages}</span>
          <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}
            className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-40">Next</button>
        </div>
      )}
    </div>
  )
}
