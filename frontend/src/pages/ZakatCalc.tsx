import { useState } from 'react'
import { calculateZakat } from '../lib/api'

const FIELDS = [
  { key: 'cash',         label: 'النقود والأرصدة البنكية',     type: 'number', unit: 'ريال' },
  { key: 'trade_goods',  label: 'عروض التجارة (المخزون)',       type: 'number', unit: 'ريال' },
  { key: 'gold_grams',   label: 'الذهب',                        type: 'number', unit: 'جرام' },
  { key: 'silver_grams', label: 'الفضة',                        type: 'number', unit: 'جرام' },
  { key: 'crops_kg',     label: 'المحاصيل الزراعية',           type: 'number', unit: 'كيلوجرام' },
  { key: 'camels',       label: 'الإبل',                        type: 'number', unit: 'رأس' },
  { key: 'cattle',       label: 'البقر والجاموس',               type: 'number', unit: 'رأس' },
  { key: 'sheep',        label: 'الغنم والماعز',                type: 'number', unit: 'رأس' },
]

const EMPTY = { cash:0, trade_goods:0, gold_grams:0, silver_grams:0, crops_kg:0, irrigated:false, camels:0, cattle:0, sheep:0 }

export default function ZakatCalc() {
  const [form,    setForm]    = useState<any>({ ...EMPTY })
  const [result,  setResult]  = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const handleCalc = async (e: any) => {
    e.preventDefault(); setLoading(true)
    try { setResult(await calculateZakat(form)) }
    finally { setLoading(false) }
  }

  const total = result?.total_zakat ?? 0

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">حاسبة الزكاة</h1>
        <p className="text-sm text-slate-400 mt-1">
          وفق الفقه الإسلامي — نصاب الزكاة: {result?.nisab?.toLocaleString('ar-SA') ?? '…'} ريال (85 جرام ذهب)
        </p>
      </div>

      <form onSubmit={handleCalc} className="card space-y-4">
        <h2 className="font-semibold text-slate-700">أدخل ما تملكه (0 إن لم ينطبق)</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {FIELDS.map(f => (
            <div key={f.key}>
              <label className="text-xs text-slate-500 block mb-1">{f.label} ({f.unit})</label>
              <input
                type="number" min={0} step={f.unit === 'ريال' ? 100 : 1}
                className="input"
                value={form[f.key]}
                onChange={e => setForm((p: any) => ({ ...p, [f.key]: Number(e.target.value) }))}
              />
            </div>
          ))}
        </div>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={form.irrigated}
            onChange={e => setForm((p: any) => ({ ...p, irrigated: e.target.checked }))} />
          المحاصيل مروية بتكلفة (5% بدلاً من 10%)
        </label>
        <button type="submit" disabled={loading} className="btn-primary w-full text-base py-3">
          {loading ? 'جارٍ الحساب…' : '⚡ احسب الزكاة'}
        </button>
      </form>

      {result && (
        <div className="space-y-4">
          {/* Results table */}
          <div className="card overflow-x-auto p-0">
            <div className="px-5 py-4 border-b border-slate-100">
              <h2 className="font-semibold text-slate-700">نتائج الحساب التفصيلية</h2>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-slate-500 text-xs">
                  <th className="px-5 py-3 text-right font-medium">الوعاء</th>
                  <th className="px-4 py-3 text-right font-medium">القيمة</th>
                  <th className="px-4 py-3 text-right font-medium">النصاب</th>
                  <th className="px-4 py-3 text-right font-medium">النسبة</th>
                  <th className="px-4 py-3 text-right font-medium">الزكاة ﷼</th>
                  <th className="px-4 py-3 text-right font-medium">الحالة</th>
                </tr>
              </thead>
              <tbody>
                {result.results.filter((r: any) => r.value > 0).map((r: any) => (
                  <tr key={r.label} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="px-5 py-3 font-medium text-slate-800">{r.label}</td>
                    <td className="px-4 py-3 text-slate-600">{r.value.toLocaleString('ar-SA')}</td>
                    <td className="px-4 py-3 text-slate-500">{r.nisab.toLocaleString('ar-SA')}</td>
                    <td className="px-4 py-3 text-slate-500">{r.rate > 0 ? `${(r.rate*100).toFixed(1)}%` : '—'}</td>
                    <td className={`px-4 py-3 font-bold ${r.zakat > 0 ? 'text-primary-600' : 'text-slate-300'}`}>
                      {r.zakat.toLocaleString('ar-SA', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-4 py-3">
                      <span className={r.eligible ? 'badge-green' : 'badge-gray'}>
                        {r.eligible ? 'واجبة' : 'دون النصاب'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Total */}
          <div className={`card text-center py-6 ${total > 0 ? 'bg-primary-50' : 'bg-slate-50'}`}>
            <p className="text-slate-500 text-sm mb-2">إجمالي الزكاة الواجبة</p>
            <p className={`text-4xl font-bold ${total > 0 ? 'text-primary-700' : 'text-slate-400'}`}>
              {total.toLocaleString('ar-SA', { minimumFractionDigits: 2 })} <span className="text-2xl">ريال</span>
            </p>
          </div>

          {/* Masaref */}
          {total > 0 && (
            <div className="card">
              <h2 className="font-semibold text-slate-700 mb-3">مصارف الزكاة الثمانية (التوبة: 60)</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {result.categories.map((cat: string) => (
                  <div key={cat} className="bg-green-50 rounded-xl p-3 text-center">
                    <p className="text-xs text-green-700 font-medium">{cat}</p>
                    <p className="text-sm font-bold text-green-800 mt-1">
                      {(total / 8).toLocaleString('ar-SA', { minimumFractionDigits: 2 })} ﷼
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <button onClick={() => { setForm({ ...EMPTY }); setResult(null) }} className="btn-secondary w-full">
            إعادة الحساب
          </button>
        </div>
      )}
    </div>
  )
}
