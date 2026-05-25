import { useEffect, useState } from 'react'
import { Search, Download, CheckSquare, UserX } from 'lucide-react'
import { contactsApi, statesApi } from '../api/client'
import { Badge } from '../components/Badge'
import type { Contact, State } from '../types'

const ROLES = ['TPO', 'Principal', 'Chairman', 'HOD', 'Dean', 'General']
const VALIDATION_STATUSES = ['unvalidated', 'valid', 'invalid']

export function Contacts() {
  const [states, setStates] = useState<State[]>([])
  const [contacts, setContacts] = useState<Contact[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [validating, setValidating] = useState(false)
  const [filters, setFilters] = useState({
    state_code: '', role: '', validation_status: '', search: ''
  })

  useEffect(() => { statesApi.list().then(setStates) }, [])
  useEffect(() => { load() }, [filters, page])

  async function load() {
    setLoading(true)
    const params: Record<string, unknown> = { page, limit: 50 }
    if (filters.state_code) params.state_code = filters.state_code
    if (filters.role) params.role = filters.role
    if (filters.validation_status) params.validation_status = filters.validation_status
    if (filters.search) params.search = filters.search
    const data = await contactsApi.list(params)
    setContacts(data.items)
    setTotal(data.total)
    setSelected(new Set())
    setLoading(false)
  }

  async function validateSelected() {
    if (selected.size === 0) return
    setValidating(true)
    await contactsApi.validate(Array.from(selected))
    setValidating(false)
    load()
  }

  function exportCsv() {
    const params: Record<string, string> = {}
    if (filters.state_code) params.state_code = filters.state_code
    if (filters.role) params.role = filters.role
    if (filters.validation_status) params.validation_status = filters.validation_status
    window.open(contactsApi.exportUrl(params), '_blank')
  }

  function toggleSelect(id: number) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  function selectAll() {
    if (selected.size === contacts.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(contacts.map(c => c.id)))
    }
  }

  const totalPages = Math.ceil(total / 50)

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Contacts</h1>
          <p className="text-slate-500 text-sm">{total.toLocaleString()} email contacts</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={validateSelected}
            disabled={selected.size === 0 || validating}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-50"
          >
            <CheckSquare size={15} />
            {validating ? 'Validating...' : `Validate (${selected.size})`}
          </button>
          <button
            onClick={exportCsv}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
          >
            <Download size={15} />
            Export CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search email or name..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-300"
            value={filters.search}
            onChange={e => setFilters(f => ({ ...f, search: e.target.value }))}
          />
        </div>
        <select className="px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none"
          value={filters.state_code} onChange={e => setFilters(f => ({ ...f, state_code: e.target.value }))}>
          <option value="">All States</option>
          {states.map(s => <option key={s.code} value={s.code}>{s.name}</option>)}
        </select>
        <select className="px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none"
          value={filters.role} onChange={e => setFilters(f => ({ ...f, role: e.target.value }))}>
          <option value="">All Roles</option>
          {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <select className="px-3 py-2 text-sm border border-slate-200 rounded-lg outline-none"
          value={filters.validation_status} onChange={e => setFilters(f => ({ ...f, validation_status: e.target.value }))}>
          <option value="">All Statuses</option>
          {VALIDATION_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {loading ? (
          <div className="flex justify-center items-center h-48">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600" />
          </div>
        ) : contacts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-slate-400">
            <p className="font-medium">No contacts found</p>
            <p className="text-sm">Try scraping colleges first from the Colleges page</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-4 py-3">
                    <input type="checkbox" checked={selected.size === contacts.length}
                      onChange={selectAll} className="rounded" />
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">Email</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">Name / Role</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">College</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">State</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">Validation</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600">Campaigns</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {contacts.map(c => (
                  <tr key={c.id} className={`hover:bg-slate-50 ${c.is_unsubscribed ? 'opacity-50' : ''}`}>
                    <td className="px-4 py-3">
                      <input type="checkbox" checked={selected.has(c.id)} onChange={() => toggleSelect(c.id)} className="rounded" />
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-slate-700">{c.email}</span>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-slate-800">{c.name || '—'}</p>
                      <Badge status={c.role} />
                    </td>
                    <td className="px-4 py-3 text-slate-600 max-w-xs truncate">{c.college_name}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs">{c.state_name}</td>
                    <td className="px-4 py-3"><Badge status={c.validation_status} /></td>
                    <td className="px-4 py-3 text-slate-500">{c.campaigns_sent}</td>
                    <td className="px-4 py-3">
                      {!c.is_unsubscribed && (
                        <button onClick={() => contactsApi.unsubscribe(c.id).then(load)}
                          className="text-slate-400 hover:text-red-500" title="Unsubscribe">
                          <UserX size={15} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

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
