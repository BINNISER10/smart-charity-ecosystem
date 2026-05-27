import { useEffect, useState } from 'react'
import { Shield, RefreshCw } from 'lucide-react'
import { getAuditLog } from '../lib/api'

const ACTION_COLOR: Record<string, string> = {
  APPLICATION_APPROVED:  'bg-green-100 text-green-700',
  APPLICATION_REJECTED:  'bg-red-100 text-red-700',
  APPLICATION_CANCELLED: 'bg-slate-100 text-slate-600',
  BENEFICIARY_ARCHIVED:  'bg-amber-100 text-amber-700',
  BENEFICIARY_RESTORED:  'bg-blue-100 text-blue-700',
  USER_REGISTERED:       'bg-violet-100 text-violet-700',
}

export default function AuditLog() {
  const [logs,    setLogs]    = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [limit,   setLimit]   = useState(50)

  const load = () => {
    setLoading(true)
    getAuditLog(limit).then(setLogs).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [limit])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">سجل التدقيق</h1>
          <p className="text-sm text-slate-400 mt-1">جميع الإجراءات والقرارات موثّقة وغير قابلة للحذف</p>
        </div>
        <div className="flex items-center gap-3">
          <select className="input w-32" value={limit}
            onChange={e => setLimit(Number(e.target.value))}>
            <option value={25}>25 سجل</option>
            <option value={50}>50 سجل</option>
            <option value={100}>100 سجل</option>
          </select>
          <button onClick={load} className="btn-secondary flex items-center gap-2">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            تحديث
          </button>
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        {loading && (
          <div className="text-center py-10 text-slate-400">جارٍ التحميل…</div>
        )}
        {!loading && logs.length === 0 && (
          <div className="text-center py-10 text-slate-400">
            <Shield size={32} className="mx-auto mb-2 opacity-30" />
            لا توجد سجلات بعد
          </div>
        )}
        {!loading && logs.slice().reverse().map((log, i) => (
          <div key={log.log_id}
               className={`flex items-start gap-4 px-6 py-4 border-b border-slate-50
                 ${i % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'} hover:bg-primary-50/30 transition-colors`}>
            {/* Timeline dot */}
            <div className="flex flex-col items-center gap-1 flex-shrink-0 pt-1">
              <div className="w-2.5 h-2.5 rounded-full bg-primary-400" />
              {i < logs.length - 1 && <div className="w-px h-6 bg-slate-200" />}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                  ${ACTION_COLOR[log.action] ?? 'bg-slate-100 text-slate-600'}`}>
                  {log.action.replace(/_/g, ' ')}
                </span>
                <span className="text-xs text-slate-400">
                  بواسطة: <strong className="text-slate-600">{log.actor}</strong>
                </span>
              </div>
              <p className="text-sm text-slate-700">{log.details}</p>
              <p className="text-xs text-slate-400 mt-1">
                {log.timestamp.slice(0, 19).replace('T', ' — ')}
              </p>
            </div>

            <span className="text-xs text-slate-300 flex-shrink-0 font-mono">{log.log_id}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
