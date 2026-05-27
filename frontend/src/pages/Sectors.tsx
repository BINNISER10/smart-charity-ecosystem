import { useEffect, useState } from 'react'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, Cell } from 'recharts'
import { getSectors } from '../lib/api'

const COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#ef4444']

export default function Sectors() {
  const [sectors, setSectors] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSectors().then(setSectors).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-center py-20 text-slate-400">جارٍ التحميل…</div>

  const radarData = sectors.map(s => ({
    sector:             s.name,
    'نسبة الاعتماد':   s.approval_rate,
    'معدل الاستفادة':  s.beneficiaries_served > 0
      ? Math.min(100, (s.beneficiaries_served / (s.total_applications || 1)) * 100)
      : 0,
  }))

  const spendData = sectors.map(s => ({ name: s.name, value: s.total_disbursed }))

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-800">القطاعات التشغيلية</h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {sectors.map((s, i) => (
          <div key={s.key} className="card space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ background: COLORS[i] }} />
              <h3 className="font-bold text-slate-800">{s.name}</h3>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {[
                ['إجمالي الطلبات',    s.total_applications],
                ['المعتمدة',           s.approved_applications],
                ['المرفوضة',           s.rejected_applications],
                ['المستفيدون',         s.beneficiaries_served],
              ].map(([label, val]) => (
                <div key={label as string} className="bg-slate-50 rounded-lg p-2">
                  <p className="text-xs text-slate-400">{label}</p>
                  <p className="font-bold text-slate-700">{val}</p>
                </div>
              ))}
            </div>
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-500">نسبة الاعتماد</span>
                <span className="font-bold text-slate-700">{s.approval_rate.toFixed(1)}%</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all"
                  style={{ width: `${s.approval_rate}%`, background: COLORS[i] }} />
              </div>
            </div>
            <div className="border-t border-slate-100 pt-2">
              <p className="text-xs text-slate-500">إجمالي الصرف</p>
              <p className="text-lg font-bold text-slate-800">{s.total_disbursed.toLocaleString('ar-SA')} <span className="text-sm font-normal text-slate-400">ريال</span></p>
            </div>
          </div>
        ))}
      </div>

      {/* Sector-specific details */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {sectors.map((s, i) => {
          const ex = s.extra ?? {}
          return (
            <div key={s.key} className="card space-y-3 border-t-4" style={{ borderTopColor: COLORS[i] }}>
              <h3 className="font-bold text-slate-700 text-sm">{s.name} — تفاصيل</h3>
              {/* Health */}
              {ex.medical_categories && (
                <div className="space-y-1">
                  <p className="text-xs text-slate-400">الفئات الطبية</p>
                  <div className="flex flex-wrap gap-1">
                    {ex.medical_categories.map((c: string) => (
                      <span key={c} className="badge-blue text-xs">{c}</span>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">حالات طارئة: <strong className="text-red-500">{ex.emergency_cases ?? 0}</strong></p>
                </div>
              )}
              {/* Housing */}
              {ex.housing_types && (
                <div className="space-y-1">
                  <p className="text-xs text-slate-400">أنواع الدعم السكني</p>
                  <div className="flex flex-wrap gap-1">
                    {ex.housing_types.map((t: string) => (
                      <span key={t} className="badge-yellow text-xs">{t}</span>
                    ))}
                  </div>
                </div>
              )}
              {/* Recycling */}
              {ex.items_by_status && (
                <div className="space-y-1">
                  <p className="text-xs text-slate-400">مستودع التدوير ({ex.total_inventory_items} صنف)</p>
                  <div className="space-y-1">
                    {Object.entries(ex.items_by_status).map(([st, cnt]: any) => (
                      <div key={st} className="flex justify-between text-xs">
                        <span className="text-slate-600">{st}</span>
                        <span className="font-bold text-slate-800">{cnt}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {/* Food */}
              {ex.total_food_batches !== undefined && (
                <div className="space-y-1">
                  <p className="text-xs text-slate-400">الدفعات الغذائية</p>
                  <div className="flex flex-wrap gap-3 text-xs">
                    <span>المسجّلة: <strong>{ex.total_food_batches}</strong></span>
                    <span>الإجمالي: <strong>{(ex.total_quantity_kg ?? 0).toFixed(0)} كجم</strong></span>
                    <span>الهدر: <strong className="text-orange-500">{(ex['waste_rate_%'] ?? 0).toFixed(1)}%</strong></span>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="font-semibold text-slate-700 mb-4">مقارنة الإنفاق بالقطاعات</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={spendData}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
              <Tooltip formatter={(v: any) => [`${v.toLocaleString('ar-SA')} ريال`]} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {spendData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2 className="font-semibold text-slate-700 mb-4">مؤشرات الأداء الشاملة</h2>
          <ResponsiveContainer width="100%" height={220}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="sector" tick={{ fontSize: 11 }} />
              <Radar name="نسبة الاعتماد" dataKey="نسبة الاعتماد" stroke="#22c55e" fill="#22c55e" fillOpacity={0.3} />
              <Radar name="معدل الاستفادة" dataKey="معدل الاستفادة" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
