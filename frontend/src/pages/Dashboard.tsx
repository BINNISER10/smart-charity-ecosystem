import { useEffect, useState } from 'react'
import {
  BarChart, Bar, PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  XAxis, YAxis, Legend
} from 'recharts'
import { Users, FileText, Wallet, Clock, TrendingUp, AlertTriangle, Brain, FileSpreadsheet } from 'lucide-react'
import { getDashboard, getAIPredictions, exportExcelUrl, exportReportUrl } from '../lib/api'

const COLORS = ['#22c55e','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899']

function StatCard({ icon: Icon, label, value, sub, color }: any) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-bold text-slate-800">{value?.toLocaleString('ar-SA') ?? '—'}</p>
        {sub && <p className="text-xs text-slate-400">{sub}</p>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [data,        setData]        = useState<any>(null)
  const [predictions, setPredictions] = useState<any>(null)
  const [loading,     setLoading]     = useState(true)
  const [error,       setError]       = useState('')

  const load = () => {
    setLoading(true)
    getDashboard()
      .then(setData)
      .catch(() => setError('تعذّر تحميل البيانات — تأكد من تشغيل الـ Backend'))
      .finally(() => setLoading(false))
    getAIPredictions().then(setPredictions).catch(() => {})
  }

  useEffect(() => { load() }, [])

  if (loading) return (
    <div className="flex items-center justify-center h-64 text-slate-400">
      <div className="text-center">
        <div className="w-10 h-10 border-4 border-primary-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p>جارٍ تحميل البيانات…</p>
      </div>
    </div>
  )

  if (error) return (
    <div className="card text-center py-12 text-red-500">
      <AlertTriangle className="mx-auto mb-2" size={32} />
      <p className="font-semibold">{error}</p>
      <button onClick={load} className="btn-primary mt-4">إعادة المحاولة</button>
    </div>
  )

  const { stats, status_distribution, sector_spending, fund_balances, recent_transactions, date: d } = data

  const statusData = Object.entries(status_distribution ?? {}).map(([name, value]) => ({ name, value }))
  const sectorData  = Object.entries(sector_spending ?? {}).map(([name, value]) => ({ name, value }))
  const fundsData   = Object.entries(fund_balances ?? {}).map(([name, value]) => ({ name, value }))

  const eff = stats.total_received > 0
    ? ((stats.total_disbursed / stats.total_received) * 100).toFixed(1)
    : '0.0'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800">لوحة التحكم الرئيسية</h1>
        <p className="text-sm text-slate-400 mt-1">
          📅 {d?.gregorian}م &nbsp;|&nbsp; {d?.hijri}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard icon={Users}       label="إجمالي المستفيدين"   value={stats.total_beneficiaries}    color="bg-primary-600"  />
        <StatCard icon={Users}       label="المؤهلون للمساعدة"   value={stats.eligible_beneficiaries} color="bg-teal-600"     />
        <StatCard icon={FileText}    label="إجمالي الطلبات"       value={stats.total_applications}     color="bg-blue-500"    />
        <StatCard icon={Clock}       label="طلبات معلقة"          value={stats.pending_applications}   color="bg-amber-500"   />
        <StatCard icon={TrendingUp}  label="إجمالي التبرعات"      value={`${(stats.total_received/1000).toFixed(0)}k ﷼`}    color="bg-violet-500"  />
        <StatCard icon={Wallet}      label="كفاءة الصرف"           value={`${eff}%`}                    color="bg-emerald-500" />
      </div>

      {/* Export Buttons */}
      <div className="flex gap-3 justify-end">
        <a href={exportExcelUrl} target="_blank" rel="noreferrer"
           className="btn-secondary flex items-center gap-1.5 text-xs">
          <FileSpreadsheet size={14} /> تصدير Excel
        </a>
        <a href={exportReportUrl} target="_blank" rel="noreferrer"
           className="btn-secondary flex items-center gap-1.5 text-xs">
          تقرير PDF
        </a>
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Distribution */}
        <div className="card">
          <h2 className="font-semibold text-slate-700 mb-4">توزيع حالات الطلبات</h2>
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={statusData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name} (${value})`} labelLine={false}>
                  {statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(v: any) => [`${v} طلب`]} />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-400 text-center py-10">لا توجد طلبات بعد</p>}
        </div>

        {/* Sector Spending */}
        <div className="card">
          <h2 className="font-semibold text-slate-700 mb-4">إنفاق القطاعات (ريال)</h2>
          {sectorData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={sectorData} layout="vertical">
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={90} />
                <Tooltip formatter={(v: any) => [`${v.toLocaleString('ar-SA')} ريال`]} />
                <Bar dataKey="value" fill="#22c55e" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-slate-400 text-center py-10">لا يوجد إنفاق بعد</p>}
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fund Balances */}
        <div className="card">
          <h2 className="font-semibold text-slate-700 mb-4">أرصدة الصناديق الأربعة</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={fundsData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(v: any) => [`${v.toLocaleString('ar-SA')} ريال`]} />
              <Bar dataKey="value" fill="#14b8a6" radius={[6, 6, 0, 0]}>
                {fundsData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Transactions */}
        <div className="card">
          <h2 className="font-semibold text-slate-700 mb-4">آخر العمليات المالية</h2>
          <div className="space-y-2">
            {recent_transactions?.length === 0 && (
              <p className="text-slate-400 text-center py-6">لا توجد عمليات بعد</p>
            )}
            {recent_transactions?.map((t: any) => (
              <div key={t.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50">
                <div className="flex items-center gap-2">
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold
                    ${t.type === 'CREDIT' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {t.type === 'CREDIT' ? '▲' : '▼'}
                  </span>
                  <div>
                    <p className="text-xs font-medium text-slate-700 truncate max-w-[140px]">{t.description}</p>
                    <p className="text-xs text-slate-400">{t.fund_type}</p>
                  </div>
                </div>
                <span className={`text-sm font-bold ${t.type === 'CREDIT' ? 'text-green-600' : 'text-red-500'}`}>
                  {t.amount.toLocaleString('ar-SA')} ﷼
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Predictions */}
      {predictions && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Brain size={18} className="text-violet-500" />
            <h2 className="font-semibold text-slate-700">تنبؤات الذكاء الاصطناعي — الاحتياجات المتوقعة للشهر القادم</h2>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {Object.entries(predictions.predictions).map(([sector, amount]: any) => (
              <div key={sector} className="bg-violet-50 rounded-xl p-4">
                <p className="text-xs text-violet-600 font-medium mb-1">{sector}</p>
                <p className="text-xl font-bold text-violet-800">{amount.toLocaleString('ar-SA')}</p>
                <p className="text-xs text-violet-400">ريال (توقع)</p>
              </div>
            ))}
          </div>
          <div className="mt-3 pt-3 border-t border-slate-100 flex gap-6 text-xs text-slate-400 flex-wrap">
            <span>حالات مدروسة: <strong className="text-slate-600">{predictions.experience_summary?.total_cases ?? 0}</strong></span>
            <span>متوسط نقاط الذكاء: <strong className="text-slate-600">{(predictions.experience_summary?.avg_score ?? 0).toFixed(1)}</strong></span>
            <span className="text-slate-300">{predictions.note}</span>
          </div>
        </div>
      )}
    </div>
  )
}
