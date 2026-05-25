import { useEffect, useState } from 'react'
import { Download, ChevronDown, ChevronUp, UserX } from 'lucide-react'
import { campaignsApi, reportsApi, contactsApi } from '../api/client'
import { Badge } from '../components/Badge'
import type { Campaign, CampaignSend } from '../types'

export function Reports() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [expanded, setExpanded] = useState<number | null>(null)
  const [sends, setSends] = useState<Record<number, CampaignSend[]>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    campaignsApi.list()
      .then(d => setCampaigns(d.items))
      .finally(() => setLoading(false))
  }, [])

  async function toggleExpand(id: number) {
    if (expanded === id) { setExpanded(null); return }
    setExpanded(id)
    if (!sends[id]) {
      const data = await reportsApi.campaignSends(id)
      setSends(prev => ({ ...prev, [id]: data.items }))
    }
  }

  async function removeFromList(contactId: number) {
    await contactsApi.unsubscribe(contactId)
    // Refresh sends for currently expanded campaign
    if (expanded) {
      const data = await reportsApi.campaignSends(expanded)
      setSends(prev => ({ ...prev, [expanded]: data.items }))
    }
  }

  const allBounced = campaigns.flatMap(c => {
    const s = sends[c.id] ?? []
    return s.filter(x => x.status === 'bounced')
  })

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Reports</h1>
        <p className="text-slate-500 text-sm">Campaign delivery and bounce reports</p>
      </div>

      {loading ? (
        <div className="flex justify-center h-48 items-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600" />
        </div>
      ) : (
        <>
          {/* Bounced emails panel */}
          {allBounced.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-5">
              <h2 className="text-sm font-semibold text-red-800 mb-3">
                Bounced Emails ({allBounced.length})
              </h2>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {allBounced.map(s => (
                  <div key={s.id} className="flex items-center justify-between text-sm">
                    <div>
                      <span className="font-mono text-red-700">{s.contact_email}</span>
                      <span className="text-red-500 ml-2 text-xs">— {s.college_name}</span>
                    </div>
                    <button onClick={() => removeFromList(s.contact_id)}
                      className="text-red-400 hover:text-red-700 flex items-center gap-1 text-xs">
                      <UserX size={13} />
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Per-campaign reports */}
          <div className="space-y-3">
            {campaigns.length === 0 && (
              <div className="bg-white rounded-xl border border-slate-200 flex items-center justify-center h-32 text-slate-400 text-sm">
                No campaigns yet
              </div>
            )}
            {campaigns.map(c => (
              <div key={c.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <div
                  className="flex items-center justify-between px-5 py-4 cursor-pointer hover:bg-slate-50"
                  onClick={() => toggleExpand(c.id)}
                >
                  <div className="flex items-center gap-3">
                    <div>
                      <p className="font-semibold text-slate-800">{c.name}</p>
                      <p className="text-xs text-slate-400">
                        {c.sent_at ? new Date(c.sent_at).toLocaleDateString() : 'Not sent yet'} · {c.template_filename}
                      </p>
                    </div>
                    <Badge status={c.status} />
                  </div>
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <p className="text-sm font-bold text-blue-600">{c.sent_count}</p>
                      <p className="text-xs text-slate-400">Sent</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-red-500">{c.bounced_count}</p>
                      <p className="text-xs text-slate-400">Bounced</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-amber-500">{c.failed_count}</p>
                      <p className="text-xs text-slate-400">Failed</p>
                    </div>
                    <a
                      href={campaignsApi.reportExportUrl(c.id)}
                      onClick={e => e.stopPropagation()}
                      className="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg"
                      title="Export CSV"
                    >
                      <Download size={16} />
                    </a>
                    {expanded === c.id ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                  </div>
                </div>

                {/* Expanded sends table */}
                {expanded === c.id && (
                  <div className="border-t border-slate-200">
                    {!sends[c.id] ? (
                      <div className="flex justify-center py-8">
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600" />
                      </div>
                    ) : sends[c.id].length === 0 ? (
                      <p className="text-sm text-slate-400 text-center py-6">No send records yet</p>
                    ) : (
                      <div className="overflow-x-auto max-h-64">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="bg-slate-50 text-xs">
                              <th className="text-left px-4 py-2.5 font-semibold text-slate-600">Email</th>
                              <th className="text-left px-4 py-2.5 font-semibold text-slate-600">Name</th>
                              <th className="text-left px-4 py-2.5 font-semibold text-slate-600">College</th>
                              <th className="text-left px-4 py-2.5 font-semibold text-slate-600">Role</th>
                              <th className="text-left px-4 py-2.5 font-semibold text-slate-600">Status</th>
                              <th className="text-left px-4 py-2.5 font-semibold text-slate-600">Sent At</th>
                              <th className="px-4 py-2.5" />
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {sends[c.id].map(s => (
                              <tr key={s.id} className="hover:bg-slate-50">
                                <td className="px-4 py-2.5 font-mono text-slate-700 text-xs">{s.contact_email}</td>
                                <td className="px-4 py-2.5 text-slate-600">{s.contact_name || '—'}</td>
                                <td className="px-4 py-2.5 text-slate-500 max-w-xs truncate">{s.college_name}</td>
                                <td className="px-4 py-2.5"><Badge status={s.role} /></td>
                                <td className="px-4 py-2.5"><Badge status={s.status} /></td>
                                <td className="px-4 py-2.5 text-slate-400 text-xs">
                                  {s.sent_at ? new Date(s.sent_at).toLocaleString() : '—'}
                                </td>
                                <td className="px-4 py-2.5">
                                  {s.status === 'bounced' && (
                                    <button onClick={() => removeFromList(s.contact_id)}
                                      className="text-red-400 hover:text-red-600">
                                      <UserX size={14} />
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
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
