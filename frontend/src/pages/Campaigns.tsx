import { useEffect, useRef, useState } from 'react'
import { Upload, Send, Eye, RefreshCw, Download } from 'lucide-react'
import { campaignsApi, statesApi } from '../api/client'
import { Badge } from '../components/Badge'
import type { Campaign, State } from '../types'

const ROLES = ['TPO', 'Principal', 'Chairman', 'HOD', 'Dean', 'General']

export function Campaigns() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [states, setStates] = useState<State[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [previewHtml, setPreviewHtml] = useState('')
  const [showPreview, setShowPreview] = useState(false)
  const [checkingBounces, setCheckingBounces] = useState<number | null>(null)
  const [sendModal, setSendModal] = useState<Campaign | null>(null)
  const [sending, setSending] = useState(false)

  const fileRef = useRef<HTMLInputElement>(null)
  const [form, setForm] = useState({ name: '', subject: '' })
  const [file, setFile] = useState<File | null>(null)
  const [sendConfig, setSendConfig] = useState({ state_codes: [] as string[], roles: [] as string[] })

  useEffect(() => {
    Promise.all([campaignsApi.list(), statesApi.list()])
      .then(([c, s]) => { setCampaigns(c.items); setStates(s) })
      .finally(() => setLoading(false))
  }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return alert('Please upload an HTML template')
    setCreating(true)
    const fd = new FormData()
    fd.append('name', form.name)
    fd.append('subject', form.subject)
    fd.append('template', file)
    await campaignsApi.create(fd)
    const updated = await campaignsApi.list()
    setCampaigns(updated.items)
    setShowCreate(false)
    setForm({ name: '', subject: '' })
    setFile(null)
    setCreating(false)
  }

  async function handleSend() {
    if (!sendModal) return
    setSending(true)
    await campaignsApi.send(sendModal.id, {
      state_codes: sendConfig.state_codes.length ? sendConfig.state_codes : undefined,
      roles: sendConfig.roles.length ? sendConfig.roles : undefined,
    })
    const updated = await campaignsApi.list()
    setCampaigns(updated.items)
    setSendModal(null)
    setSending(false)
  }

  async function checkBounces(id: number) {
    setCheckingBounces(id)
    await campaignsApi.checkBounces(id)
    const updated = await campaignsApi.list()
    setCampaigns(updated.items)
    setCheckingBounces(null)
  }

  async function previewCampaign(id: number) {
    const c = await campaignsApi.get(id)
    setPreviewHtml(c.template_html)
    setShowPreview(true)
  }

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    const reader = new FileReader()
    reader.onload = ev => setPreviewHtml(ev.target?.result as string)
    reader.readAsText(f)
  }

  function toggleStateCode(code: string) {
    setSendConfig(c => ({
      ...c,
      state_codes: c.state_codes.includes(code)
        ? c.state_codes.filter(s => s !== code)
        : [...c.state_codes, code],
    }))
  }

  function toggleRole(role: string) {
    setSendConfig(c => ({
      ...c,
      roles: c.roles.includes(role) ? c.roles.filter(r => r !== role) : [...c.roles, role],
    }))
  }

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Campaigns</h1>
          <p className="text-slate-500 text-sm">{campaigns.length} campaigns total</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
        >
          <Upload size={15} />
          New Campaign
        </button>
      </div>

      {/* Campaign list */}
      {loading ? (
        <div className="flex justify-center h-48 items-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600" />
        </div>
      ) : campaigns.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 flex flex-col items-center justify-center h-48 text-slate-400">
          <p className="font-medium">No campaigns yet</p>
          <p className="text-sm">Click "New Campaign" to create your first one</p>
        </div>
      ) : (
        <div className="space-y-3">
          {campaigns.map(c => (
            <div key={c.id} className="bg-white rounded-xl border border-slate-200 p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-slate-800">{c.name}</h3>
                    <Badge status={c.status} />
                  </div>
                  <p className="text-sm text-slate-500 truncate">Subject: {c.subject}</p>
                  <p className="text-xs text-slate-400 mt-1">{c.template_filename}</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button onClick={() => previewCampaign(c.id)}
                    className="p-2 text-slate-500 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg" title="Preview">
                    <Eye size={16} />
                  </button>
                  {c.status === 'sent' && (
                    <button onClick={() => checkBounces(c.id)} disabled={checkingBounces === c.id}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-50">
                      {checkingBounces === c.id ? <RefreshCw size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                      Check Bounces
                    </button>
                  )}
                  {c.status !== 'sending' && (
                    <button onClick={() => { setSendModal(c); setSendConfig({ state_codes: [], roles: [] }) }}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700">
                      <Send size={13} />
                      Send
                    </button>
                  )}
                  <a href={campaignsApi.reportExportUrl(c.id)}
                    className="p-2 text-slate-500 hover:text-green-600 hover:bg-green-50 rounded-lg" title="Download report">
                    <Download size={16} />
                  </a>
                </div>
              </div>

              {/* Stats bar */}
              <div className="mt-4 grid grid-cols-4 gap-3">
                {[
                  { label: 'Recipients', value: c.total_recipients, color: 'text-slate-600' },
                  { label: 'Sent', value: c.sent_count, color: 'text-blue-600' },
                  { label: 'Bounced', value: c.bounced_count, color: 'text-red-600' },
                  { label: 'Failed', value: c.failed_count, color: 'text-amber-600' },
                ].map(s => (
                  <div key={s.label} className="bg-slate-50 rounded-lg p-3 text-center">
                    <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
                    <p className="text-xs text-slate-500">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create campaign modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg p-6 shadow-xl">
            <h2 className="text-lg font-bold text-slate-800 mb-4">New Campaign</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Campaign Name</label>
                <input required type="text" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-indigo-300"
                  placeholder="e.g. May 2025 TPO Outreach" />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Email Subject</label>
                <input required type="text" value={form.subject} onChange={e => setForm(f => ({ ...f, subject: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-indigo-300"
                  placeholder="e.g. Exciting Placement Opportunity for Your Students" />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">HTML Template</label>
                <div
                  onClick={() => fileRef.current?.click()}
                  className="border-2 border-dashed border-slate-200 rounded-lg p-6 text-center cursor-pointer hover:border-indigo-300"
                >
                  <Upload size={24} className="mx-auto text-slate-400 mb-2" />
                  <p className="text-sm text-slate-500">
                    {file ? file.name : 'Click to upload HTML template'}
                  </p>
                </div>
                <input ref={fileRef} type="file" accept=".html,.htm" className="hidden" onChange={onFileChange} />
              </div>
              {previewHtml && file && (
                <div className="border rounded-lg overflow-hidden">
                  <p className="text-xs font-medium text-slate-500 px-3 py-2 bg-slate-50 border-b">Preview</p>
                  <iframe srcDoc={previewHtml} className="w-full h-48" sandbox="allow-same-origin" />
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowCreate(false)}
                  className="flex-1 px-4 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50">
                  Cancel
                </button>
                <button type="submit" disabled={creating}
                  className="flex-1 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
                  {creating ? 'Creating...' : 'Create Campaign'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Send modal */}
      {sendModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg p-6 shadow-xl">
            <h2 className="text-lg font-bold text-slate-800 mb-1">Send Campaign</h2>
            <p className="text-sm text-slate-500 mb-4">{sendModal.name}</p>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">Target States (leave empty = all)</p>
                <div className="flex flex-wrap gap-2">
                  {states.map(s => (
                    <button key={s.code} type="button"
                      onClick={() => toggleStateCode(s.code)}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                        sendConfig.state_codes.includes(s.code)
                          ? 'bg-indigo-600 text-white border-indigo-600'
                          : 'border-slate-200 text-slate-600 hover:border-indigo-300'
                      }`}>
                      {s.name}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-700 mb-2">Target Roles (leave empty = all)</p>
                <div className="flex flex-wrap gap-2">
                  {ROLES.map(r => (
                    <button key={r} type="button"
                      onClick={() => toggleRole(r)}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                        sendConfig.roles.includes(r)
                          ? 'bg-indigo-600 text-white border-indigo-600'
                          : 'border-slate-200 text-slate-600 hover:border-indigo-300'
                      }`}>
                      {r}
                    </button>
                  ))}
                </div>
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm text-amber-800">
                Emails will be sent 2 seconds apart via ready4industry@gmail.com. Gmail allows ~500/day.
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setSendModal(null)}
                className="flex-1 px-4 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50">
                Cancel
              </button>
              <button onClick={handleSend} disabled={sending}
                className="flex-1 px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
                {sending ? 'Starting...' : 'Confirm & Send'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview modal */}
      {showPreview && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-xl">
            <div className="flex items-center justify-between px-5 py-4 border-b">
              <h2 className="font-semibold text-slate-800">Template Preview</h2>
              <button onClick={() => setShowPreview(false)} className="text-slate-400 hover:text-slate-700">✕</button>
            </div>
            <iframe srcDoc={previewHtml} className="flex-1 w-full" sandbox="allow-same-origin" />
          </div>
        </div>
      )}
    </div>
  )
}
