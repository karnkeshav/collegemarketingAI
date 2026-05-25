interface Props {
  status: string
}

const styles: Record<string, string> = {
  valid: 'bg-green-100 text-green-700',
  invalid: 'bg-red-100 text-red-700',
  unvalidated: 'bg-slate-100 text-slate-600',
  pending: 'bg-amber-100 text-amber-700',
  sent: 'bg-blue-100 text-blue-700',
  bounced: 'bg-red-100 text-red-700',
  failed: 'bg-red-100 text-red-700',
  done: 'bg-green-100 text-green-700',
  scraping: 'bg-amber-100 text-amber-700',
  draft: 'bg-slate-100 text-slate-600',
  sending: 'bg-amber-100 text-amber-700',
  TPO: 'bg-indigo-100 text-indigo-700',
  Principal: 'bg-purple-100 text-purple-700',
  Chairman: 'bg-blue-100 text-blue-700',
  HOD: 'bg-teal-100 text-teal-700',
  Dean: 'bg-pink-100 text-pink-700',
  General: 'bg-slate-100 text-slate-600',
}

export function Badge({ status }: Props) {
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${styles[status] ?? 'bg-slate-100 text-slate-600'}`}>
      {status}
    </span>
  )
}
