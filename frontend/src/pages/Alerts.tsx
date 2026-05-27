import { useEffect, useState } from 'react'
import { AlertTriangle, AlertCircle, RefreshCw, CheckCircle } from 'lucide-react'
import { getAlerts } from '../lib/api'

export default function Alerts() {
  const [data,    setData]    = useState<any>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    getAlerts().then(setData).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const alerts     = data?.alerts ?? []
  const criticals  = alerts.filter((a: any) => a.level === 'CRITICAL')
  const warnings   = alerts.filter((a: any) => a.level === 'WARNING')

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">التنبيهات ومراقبة النظام</h1>
          <p className="text-sm text-slate-400 mt-1">مراقبة تلقائية للأرصدة والطلبات المعلقة</p>
        </div>
        <button onClick={load} className="btn-secondary flex items-center gap-2">
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          تحديث
        </button>
      </div>

      {/* Summary */}
      {!loading && (
        <div className="grid grid-cols-3 gap-4">
          <div className={`card text-center ${criticals.length > 0 ? 'bg-red-50' : 'bg-white'}`}>
            <AlertTriangle size={24} className={`mx-auto mb-2 ${criticals.length > 0 ? 'text-red-500' : 'text-slate-300'}`} />
            <p className="text-3xl font-bold text-red-600">{criticals.length}</p>
            <p className="text-xs text-slate-500 mt-1">تنبيهات حرجة</p>
          </div>
          <div className={`card text-center ${warnings.length > 0 ? 'bg-amber-50' : 'bg-white'}`}>
            <AlertCircle size={24} className={`mx-auto mb-2 ${warnings.length > 0 ? 'text-amber-500' : 'text-slate-300'}`} />
            <p className="text-3xl font-bold text-amber-600">{warnings.length}</p>
            <p className="text-xs text-slate-500 mt-1">تحذيرات</p>
          </div>
          <div className={`card text-center ${alerts.length === 0 ? 'bg-green-50' : 'bg-white'}`}>
            <CheckCircle size={24} className={`mx-auto mb-2 ${alerts.length === 0 ? 'text-green-500' : 'text-slate-300'}`} />
            <p className="text-3xl font-bold text-green-600">{alerts.length === 0 ? '✓' : alerts.length}</p>
            <p className="text-xs text-slate-500 mt-1">{alerts.length === 0 ? 'النظام سليم' : 'إجمالي'}</p>
          </div>
        </div>
      )}

      {loading && <div className="card text-center py-10 text-slate-400">جارٍ الفحص…</div>}

      {!loading && alerts.length === 0 && (
        <div className="card text-center py-16">
          <CheckCircle size={48} className="mx-auto mb-3 text-green-400" />
          <p className="text-xl font-bold text-green-600">النظام يعمل بشكل سليم</p>
          <p className="text-sm text-slate-400 mt-1">لا توجد تنبيهات أو تحذيرات حالياً</p>
        </div>
      )}

      {/* Critical */}
      {criticals.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-semibold text-red-700 flex items-center gap-2">
            <AlertTriangle size={16} /> تنبيهات حرجة تستوجب تدخلاً فورياً
          </h2>
          {criticals.map((a: any, i: number) => (
            <div key={i} className="card border-r-4 border-red-500 bg-red-50 flex items-start gap-4">
              <AlertTriangle size={20} className="text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="badge-red">حرج</span>
                  <span className="text-sm font-bold text-slate-700">{a.category}</span>
                </div>
                <p className="text-sm text-red-700">{a.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-semibold text-amber-700 flex items-center gap-2">
            <AlertCircle size={16} /> تحذيرات تحتاج متابعة
          </h2>
          {warnings.map((a: any, i: number) => (
            <div key={i} className="card border-r-4 border-amber-400 bg-amber-50 flex items-start gap-4">
              <AlertCircle size={20} className="text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="badge-yellow">تحذير</span>
                  <span className="text-sm font-bold text-slate-700">{a.category}</span>
                </div>
                <p className="text-sm text-amber-700">{a.message}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
