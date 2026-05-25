import type { ComponentType } from 'react'

interface Props {
  title: string
  value: number | string
  icon: ComponentType<{ size?: number; className?: string }>
  color?: string
  sub?: string
}

export function StatsCard({ title, value, icon: Icon, color = 'indigo', sub }: Props) {
  const colorMap: Record<string, string> = {
    indigo: 'bg-indigo-50 text-indigo-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    amber: 'bg-amber-50 text-amber-600',
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-purple-50 text-purple-600',
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 flex items-start gap-4">
      <div className={`p-3 rounded-lg ${colorMap[color] ?? colorMap.indigo}`}>
        <Icon size={22} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-slate-500 text-sm">{title}</p>
        <p className="text-2xl font-bold text-slate-800 mt-0.5">{value.toLocaleString()}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}
