import { useEffect, useState } from 'react'
import { Shield, BookOpen, ChevronDown, ChevronUp } from 'lucide-react'
import { getConfigRules, getConfigStructure } from '../lib/api'

function Section({ title, children, defaultOpen = false }: any) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="card overflow-hidden">
      <button
        className="w-full flex items-center justify-between p-4 text-right hover:bg-slate-50 transition-colors"
        onClick={() => setOpen(o => !o)}
      >
        <span className="font-bold text-slate-700">{title}</span>
        {open ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  )
}

function KV({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex items-start justify-between py-1.5 border-b border-slate-50 last:border-0 text-sm">
      <span className="text-slate-500 shrink-0 ml-4">{label}</span>
      <span className="font-medium text-slate-800 text-left">{String(value)}</span>
    </div>
  )
}

export default function Config() {
  const [rules,     setRules]     = useState<any>(null)
  const [structure, setStructure] = useState<any>(null)
  const [loading,   setLoading]   = useState(true)

  useEffect(() => {
    Promise.all([getConfigRules(), getConfigStructure()])
      .then(([r, s]) => { setRules(r); setStructure(s) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="text-center py-20 text-slate-400">جارٍ التحميل…</div>

  const zakah     = rules?.zakah     ?? {}
  const eligib    = rules?.eligibility ?? {}
  const apprLimits= rules?.approval_limits ?? {}
  const funds     = rules?.funds     ?? {}
  const sectors   = structure?.sectors ?? []
  const authority = structure?.authority_matrix ?? {}
  const workflow  = structure?.workflow ?? {}

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">القواعد الشرعية والهيكل التنظيمي</h1>
        <p className="text-sm text-slate-400 mt-1">
          مصدر البيانات: <code className="bg-slate-100 px-1 rounded">config/rules.json</code> &nbsp;+&nbsp;
          <code className="bg-slate-100 px-1 rounded">config/structure.json</code>
        </p>
      </div>

      {/* Zakah Rules */}
      <Section title="📋 قواعد الزكاة الشرعية" defaultOpen>
        <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 mb-4 text-sm text-amber-800 font-medium">
          {zakah.condition}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-slate-400 font-semibold mb-2 uppercase tracking-wide">المصارف الثمانية</p>
            <div className="space-y-1">
              {(zakah.categories ?? []).map((c: string, i: number) => (
                <div key={c} className="flex items-center gap-2 text-sm">
                  <span className="w-5 h-5 rounded-full bg-primary-100 text-primary-700 text-xs flex items-center justify-center font-bold">{i + 1}</span>
                  <span className="text-slate-700">{c}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="space-y-2">
            <KV label="نصاب الذهب"        value={`${zakah.nisab_gold_grams} غرام`} />
            <KV label="نصاب الفضة"        value={`${zakah.nisab_silver_grams} غرام`} />
            <KV label="نسبة الزكاة"       value={`${((zakah.zakat_rate ?? 0.025) * 100).toFixed(1)}%`} />
            <KV label="سعر الذهب (ريال/غ)" value={`${zakah.gold_price_per_gram_sar} ريال`} />
            <KV label="حد الدخل الشهري"   value={`${zakah.income_threshold_monthly_sar?.toLocaleString('ar-SA')} ريال`} />
            <KV label="أقصى نسبة تخصيص"  value={`${((zakah.max_allocation_ratio ?? 0.125) * 100)}%`} />
          </div>
        </div>
      </Section>

      {/* Eligibility */}
      <Section title="✅ شروط الأهلية ومعايير الاستحقاق">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(eligib.income_limits ?? {}).map(([k, v]: any) => (
            <div key={k} className="bg-green-50 rounded-xl p-3 text-center">
              <p className="text-xs text-green-600 mb-1">{k.replace('family_','أسرة ').replace('single','فرد')}</p>
              <p className="text-xl font-bold text-green-800">{v.toLocaleString('ar-SA')}</p>
              <p className="text-xs text-green-500">ريال/شهر</p>
            </div>
          ))}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-3">
          <KV label="علاوة ذوي الإعاقة"    value={`${eligib.disability_bonus_income?.toLocaleString('ar-SA')} ريال`} />
          <KV label="الحد الأقصى للدخل"    value={`${eligib.max_monthly_income_sar?.toLocaleString('ar-SA')} ريال`} />
        </div>
      </Section>

      {/* Approval Limits */}
      <Section title="🔐 مصفوفة صلاحيات الاعتماد">
        <div className="space-y-2">
          {Object.entries(authority).map(([role, info]: any) => (
            <div key={role} className="flex items-center justify-between p-3 rounded-xl bg-slate-50">
              <div className="flex items-center gap-3">
                <Shield size={14} className="text-slate-400" />
                <div>
                  <p className="font-medium text-slate-700 text-sm">{info.label}</p>
                  <p className="text-xs text-slate-400">{role}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className={info.can_approve ? 'badge-green' : 'badge-gray'}>موافقة</span>
                <span className={info.can_disburse ? 'badge-green' : 'badge-gray'}>صرف</span>
                <span className="font-bold text-slate-700 bg-white rounded-lg px-2 py-1">
                  {info.approval_limit >= 9999999 ? '∞' : info.approval_limit?.toLocaleString('ar-SA') + ' ريال'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* Funds */}
      <Section title="🏦 الصناديق المالية الأربعة">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {Object.entries(funds).map(([key, info]: any) => (
            <div key={key} className="border border-slate-100 rounded-xl p-4">
              <p className="font-bold text-slate-700 mb-1">{key}</p>
              <p className="text-sm text-slate-500">{info.description}</p>
              <p className="text-xs mt-2">
                <span className={`badge ${info.transferable ? 'badge-green' : 'badge-red'}`}>
                  {info.transferable ? 'قابل للتحويل' : 'غير قابل للتحويل'}
                </span>
              </p>
            </div>
          ))}
        </div>
      </Section>

      {/* Sectors */}
      <Section title="🏢 القطاعات التشغيلية وأهدافها">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          {sectors.map((s: any) => (
            <div key={s.key} className="border border-slate-100 rounded-xl p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-2xl">{s.icon}</span>
                <p className="font-bold text-slate-700">{s.name_ar}</p>
              </div>
              <p className="text-xs text-slate-400">الصندوق: <strong className="text-slate-600">{s.fund}</strong></p>
              <p className="text-xs text-slate-400">الأولوية: <strong className="text-slate-600">{s.priority}</strong></p>
              {s.kpi_targets && (
                <div className="space-y-1 pt-1 border-t border-slate-50">
                  {Object.entries(s.kpi_targets).map(([k, v]: any) => (
                    <div key={k} className="flex justify-between text-xs">
                      <span className="text-slate-400">{k.replace(/_/g, ' ')}</span>
                      <span className="font-medium text-slate-700">{String(v)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>

      {/* Workflow */}
      <Section title="🔄 مسار معالجة الطلبات">
        <div className="flex flex-wrap gap-2 mb-4">
          {(workflow.application_states ?? []).map((s: string, i: number) => (
            <div key={s} className="flex items-center gap-1">
              <span className="badge-blue text-xs">{s}</span>
              {i < (workflow.application_states?.length ?? 0) - 1 && (
                <span className="text-slate-300 text-xs">←</span>
              )}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-3 gap-3">
          {Object.entries(workflow.sla_days ?? {}).map(([step, days]: any) => (
            <div key={step} className="bg-blue-50 rounded-xl p-3 text-center">
              <p className="text-xs text-blue-500 mb-1">{step.replace(/_/g, ' ')}</p>
              <p className="text-2xl font-bold text-blue-800">{days}</p>
              <p className="text-xs text-blue-400">يوم</p>
            </div>
          ))}
        </div>
      </Section>
    </div>
  )
}
