import { useEffect, useState } from 'react'
import { TrendingUp, TrendingDown, PlusCircle, Users, FileSpreadsheet, FileText } from 'lucide-react'
import { getFinanceReport, getTransactions, donate, getEnums, getDonors, exportExcelUrl, exportReportUrl } from '../lib/api'

export default function Finance() {
  const [report,     setReport]     = useState<any>(null)
  const [txns,       setTxns]       = useState<any[]>([])
  const [donors,     setDonors]     = useState<any[]>([])
  const [enums,      setEnums]      = useState<any>({})
  const [tab,        setTab]        = useState<'txns'|'donors'>('txns')
  const [showDonate, setShowDonate] = useState(false)
  const [form,       setForm]       = useState({ donor_name:'', donor_phone:'', amount:'', fund_type:'' })
  const [saving,     setSaving]     = useState(false)
  const [msg,        setMsg]        = useState('')

  const load = () => {
    getFinanceReport().then(setReport)
    getTransactions({ limit: 30 }).then(setTxns)
    getDonors().then(setDonors)
  }

  useEffect(() => { load(); getEnums().then(setEnums) }, [])

  const handleDonate = async (e: any) => {
    e.preventDefault(); setSaving(true); setMsg('')
    try {
      const res = await donate({ ...form, amount: Number(form.amount) })
      setMsg(`✓ ${res.message}`)
      setForm({ donor_name:'', donor_phone:'', amount:'', fund_type:'' })
      load()
    } catch (err: any) {
      setMsg(`✗ ${err.response?.data?.detail ?? 'حدث خطأ'}`)
    } finally { setSaving(false) }
  }

  if (!report) return <div className="text-center py-20 text-slate-400">جارٍ التحميل…</div>

  const { balances, total_received, total_disbursed, total_transactions, total_donors } = report
  const net = total_received - total_disbursed
  const eff = total_received > 0 ? ((total_disbursed / total_received) * 100).toFixed(1) : '0.0'

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-slate-800">المالية</h1>
        <div className="flex items-center gap-2">
          <a href={exportExcelUrl} target="_blank" rel="noreferrer"
             className="btn-secondary flex items-center gap-1.5 text-xs">
            <FileSpreadsheet size={14} /> تصدير Excel
          </a>
          <a href={exportReportUrl} target="_blank" rel="noreferrer"
             className="btn-secondary flex items-center gap-1.5 text-xs">
            <FileText size={14} /> تقرير PDF
          </a>
          <button onClick={() => { setShowDonate(true); setMsg('') }} className="btn-primary flex items-center gap-2">
            <PlusCircle size={16} /> تسجيل تبرع
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'إجمالي التبرعات',   value: total_received,     color: 'text-green-600',  bg: 'bg-green-50' },
          { label: 'إجمالي الصرف',       value: total_disbursed,    color: 'text-blue-600',   bg: 'bg-blue-50'  },
          { label: 'الرصيد الصافي',      value: net,                color: net>=0?'text-emerald-600':'text-red-500', bg: 'bg-slate-50' },
          { label: 'كفاءة الصرف',         value: `${eff}%`,          color: 'text-violet-600', bg: 'bg-violet-50'},
        ].map(({ label, value, color, bg }) => (
          <div key={label} className={`card text-center ${bg}`}>
            <p className="text-xs text-slate-500 mb-1">{label}</p>
            <p className={`text-2xl font-bold ${color}`}>
              {typeof value === 'number' ? `${value.toLocaleString('ar-SA')} ﷼` : value}
            </p>
          </div>
        ))}
      </div>

      {/* Fund balances */}
      <div className="card">
        <h2 className="font-semibold text-slate-700 mb-4">أرصدة الصناديق الأربعة</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {Object.entries(balances ?? {}).map(([name, val]: any) => (
            <div key={name} className="bg-slate-50 rounded-xl p-4 text-center">
              <p className="text-xs text-slate-500 mb-1">{name}</p>
              <p className="text-xl font-bold text-slate-800">{val.toLocaleString('ar-SA')}</p>
              <p className="text-xs text-slate-400">ريال</p>
              <div className="mt-2 h-1.5 rounded-full bg-slate-200 overflow-hidden">
                <div className="h-full bg-primary-500 rounded-full"
                  style={{ width: `${Math.min(100, (val / (total_received || 1)) * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex gap-6 text-sm text-slate-500 border-t border-slate-100 pt-4">
          <span>عدد العمليات: <strong className="text-slate-700">{total_transactions}</strong></span>
          <span>عدد المتبرعين: <strong className="text-slate-700">{total_donors}</strong></span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
        <button onClick={() => setTab('txns')}
          className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${tab==='txns' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}>
          العمليات المالية
        </button>
        <button onClick={() => setTab('donors')}
          className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${tab==='donors' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}>
          <Users size={14} /> المتبرعون ({donors.length})
        </button>
      </div>

      {/* Transactions */}
      {tab === 'txns' && <div className="card overflow-x-auto p-0">
        <div className="px-5 py-4 border-b border-slate-100">
          <h2 className="font-semibold text-slate-700">سجل العمليات المالية</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-slate-500 text-xs">
              <th className="px-5 py-3 text-right font-medium">النوع</th>
              <th className="px-4 py-3 text-right font-medium">الوصف</th>
              <th className="px-4 py-3 text-right font-medium">الصندوق</th>
              <th className="px-4 py-3 text-right font-medium">المبلغ ﷼</th>
              <th className="px-4 py-3 text-right font-medium">الرصيد بعد ﷼</th>
              <th className="px-4 py-3 text-right font-medium">التاريخ</th>
            </tr>
          </thead>
          <tbody>
            {txns.length === 0 && (
              <tr><td colSpan={6} className="text-center py-10 text-slate-400">لا توجد عمليات</td></tr>
            )}
            {txns.map(t => (
              <tr key={t.id} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    {t.type === 'CREDIT'
                      ? <TrendingUp size={14} className="text-green-500" />
                      : <TrendingDown size={14} className="text-red-500" />}
                    <span className={t.type === 'CREDIT' ? 'text-green-600 font-medium' : 'text-red-500 font-medium'}>
                      {t.type === 'CREDIT' ? 'إيداع' : 'صرف'}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-600 max-w-[200px] truncate">{t.description}</td>
                <td className="px-4 py-3 text-slate-600">{t.fund_type}</td>
                <td className={`px-4 py-3 font-bold ${t.type === 'CREDIT' ? 'text-green-600' : 'text-red-500'}`}>
                  {t.type === 'CREDIT' ? '+' : '-'}{t.amount.toLocaleString('ar-SA')}
                </td>
                <td className="px-4 py-3 text-slate-700">{t.balance_after.toLocaleString('ar-SA')}</td>
                <td className="px-4 py-3 text-slate-400 text-xs">{t.timestamp.slice(0, 16).replace('T', ' ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>}

      {/* Donors Table */}
      {tab === 'donors' && <div className="card overflow-x-auto p-0">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-semibold text-slate-700">سجل المتبرعين</h2>
          <span className="text-xs text-slate-400">{donors.length} متبرع مسجّل</span>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-slate-500 text-xs">
              <th className="px-5 py-3 text-right font-medium">الاسم</th>
              <th className="px-4 py-3 text-right font-medium">الهاتف</th>
              <th className="px-4 py-3 text-right font-medium">الصندوق</th>
              <th className="px-4 py-3 text-right font-medium">إجمالي التبرعات ﷼</th>
              <th className="px-4 py-3 text-right font-medium">عدد المرات</th>
              <th className="px-4 py-3 text-right font-medium">أول تبرع</th>
            </tr>
          </thead>
          <tbody>
            {donors.length === 0 && (
              <tr><td colSpan={6} className="text-center py-10 text-slate-400">لا يوجد متبرعون</td></tr>
            )}
            {donors.map(d => (
              <tr key={d.donor_id} className="border-b border-slate-50 hover:bg-slate-50">
                <td className="px-5 py-3 font-medium text-slate-800">{d.full_name}</td>
                <td className="px-4 py-3 text-slate-500">{d.phone}</td>
                <td className="px-4 py-3">
                  <span className="badge-blue">{d.fund_type}</span>
                </td>
                <td className="px-4 py-3 font-bold text-green-600">{d.total_donated.toLocaleString('ar-SA')}</td>
                <td className="px-4 py-3 text-center text-slate-600">{d.donation_count}</td>
                <td className="px-4 py-3 text-slate-400 text-xs">
                  <div>{d.first_donation_date}</div>
                  <div className="text-slate-300">{d.first_donation_date_h}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>}

      {/* Donate Modal */}
      {showDonate && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
             onClick={() => setShowDonate(false)}>
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 space-y-4"
               onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-lg">تسجيل تبرع جديد</h3>
              <button onClick={() => setShowDonate(false)} className="text-slate-400">✕</button>
            </div>
            {msg && (
              <div className={`text-sm p-3 rounded-lg ${msg.startsWith('✓') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                {msg}
              </div>
            )}
            <form onSubmit={handleDonate} className="space-y-3">
              <div>
                <label className="text-xs text-slate-500 block mb-1">اسم المتبرع *</label>
                <input required className="input" value={form.donor_name}
                  onChange={e => setForm(f => ({ ...f, donor_name: e.target.value }))} />
              </div>
              <div>
                <label className="text-xs text-slate-500 block mb-1">هاتف المتبرع *</label>
                <input required className="input" value={form.donor_phone}
                  onChange={e => setForm(f => ({ ...f, donor_phone: e.target.value }))} />
              </div>
              <div>
                <label className="text-xs text-slate-500 block mb-1">قيمة التبرع (ريال) *</label>
                <input required type="number" min={1} step={100} className="input" value={form.amount}
                  onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} />
              </div>
              <div>
                <label className="text-xs text-slate-500 block mb-1">الصندوق *</label>
                <select required className="input" value={form.fund_type}
                  onChange={e => setForm(f => ({ ...f, fund_type: e.target.value }))}>
                  <option value="">اختر الصندوق…</option>
                  {enums.fund_types?.map((ft: string) => <option key={ft} value={ft}>{ft}</option>)}
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={saving} className="btn-primary flex-1">
                  {saving ? 'جارٍ التسجيل…' : 'تسجيل التبرع'}
                </button>
                <button type="button" onClick={() => setShowDonate(false)} className="btn-secondary">إلغاء</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
