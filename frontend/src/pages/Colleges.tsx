import { useEffect, useRef, useState } from 'react'
import { Search, RefreshCw, ExternalLink, Play, Upload, Download } from 'lucide-react'
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
  const [showImport, setShowImport] = useState(false)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<{ added: number; skipped_duplicates: number; message: string } | null>(null)
  const [filters, setFilters] = useState({ state_code: '', college_type: '', search: '' })
  const fileRef = useRef<HTMLInputElement>(null)

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
    const interval = setInterval(async () => {
      const status = await scraperApi.status()
      if (status[stateCode]?.status === 'done' || status[stateCode]?.status === 'failed') {
        clearInterval(interval)
        setScraping(null)
        load()
      }
    }, 3000)
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setImporting(true)
    setImportResult(null)
    const fd = new FormData()
    fd.append('file', file)
    try {
      const result = await collegesApi.importCsv(fd)
      setImportResult(result)
      load()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Import failed'
      setImportResult({ added: 0, skipped_duplicates: 0, message: msg })
    }
    setImporting(false)
    if (fileRef.current) fileRef.current.value = ''
  }

  const totalPages = Math.ceil(total / 50)

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Colleges</h1>
          <p className="text-slate-500 text-sm">{total.toLocaleString()} colleges · Click a state to scrape websites for emails</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {/* Import CSV */}
          <button
            onClick={() => setShowImport(v => !v)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 hover:bg-slate-50"
          >
            <Upload size={13} />
            Import CSV
          </button>

          {/* Scrape per state */}
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

      {/* Import panel */}
      {showImport && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 space-y-3">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-semibold text-blue-800">Import Colleges from CSV</p>
              <p className="text-xs text-blue-600 mt-0.5">
                Upload a CSV with columns: <code className="bg-blue-100 px-1 rounded">name, city, state_code, website, college_type</code>
              </p>
            </div>
            <a
              href={collegesApi.templateUrl()}
              className="flex items-center gap-1 text-xs text-blue-700 hover:text-blue-900 underline"
            >
              <Download size={13} />
              Download template
            </a>
          </div>

          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 px-4 py-2 bg-white border border-blue-300 rounded-lg cursor-pointer text-sm text-blue-700 hover:bg-blue-50">
              <Upload size={15} />
              {importing ? 'Importing...' : 'Choose CSV file'}
              <input
                ref={fileRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={handleImport}
                disabled={importing}
              />
            </label>
            <p className="text-xs text-blue-600">
              Use <strong>state_code</strong>: TS (Telangana), AP (Andhra Pradesh), BR (Bihar), JH (Jharkhand), DL (Delhi)
            </p>
          </div>

          {importResult && (
            <div className={`text-sm px-3 py-2 rounded-lg ${importResult.added > 0 ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}`}>
              {importResult.message}
            </div>
          )}

          <p className="text-xs text-blue-500">
            After importing, click <strong>Scrape [State]</strong> to visit each college website and extract email addresses.
          </p>
        </div>
      )}

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
          <div className="flex flex-col items-center justify-center h-64 text-slate-400 gap-2">
            <p className="font-medium text-slate-600">No colleges yet</p>
            <p className="text-sm text-center max-w-sm">
              Two ways to add colleges:
            </p>
            <ol className="text-sm text-slate-500 list-decimal list-inside text-left space-y-1 mt-1">
              <li>Click <strong className="text-indigo-600">Import CSV</strong> above → upload a list of colleges with their websites</li>
              <li>Click <strong className="text-indigo-600">Scrape [State]</strong> → auto-fetches from AICTE portal (may be down occasionally)</li>
            </ol>
            <button
              onClick={() => setShowImport(true)}
              className="mt-3 flex items-center gap-2 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              <Upload size={15} />
              Import CSV now
            </button>
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
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">Actions</th>
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
                    <td className="px-4 py-3 flex items-center gap-2">
                      {c.website ? (
                        <a href={c.website} target="_blank" rel="noopener noreferrer"
                          className="text-indigo-500 hover:text-indigo-700">
                          <ExternalLink size={14} />
                        </a>
                      ) : null}
                      <button
                        onClick={() => scraperApi.start(undefined, c.id).then(load)}
                        className="text-slate-400 hover:text-indigo-600"
                        title="Scrape this college"
                      >
                        <Play size={14} />
                      </button>
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
