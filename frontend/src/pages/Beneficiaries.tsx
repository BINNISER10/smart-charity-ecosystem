import { useEffect, useState } from 'react'
import { UserPlus, Search, Archive, RotateCcw, Eye, Pencil } from 'lucide-react'
import {
  getBeneficiaries, createBeneficiary, archiveBeneficiary,
  restoreBeneficiary, getBeneficiaryDetail, updateBeneficiary
} from '../lib/api'

function Badge({ eligible }: { eligible: boolean }) {
  return (
    <span className={eligible ? 'badge-green' : 'badge-red'}>
      {eligible ? 'مؤهل ✓' : 'غير مؤهل ✗'}
    </span>
  )
}

function DetailModal({ id, onClose }: { id: string; onClose: () => void }) {
  const [data, setData] = useState<any>(null)
  useEffect(() => { getBeneficiaryDetail(id).then(setData) }, [id])
  if (!data) return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl p-8"><p className="text-slate-500">جارٍ التحميل…</p></div>
    </div>
  )
  const { beneficiary: b, applications, total_disbursed, disbursed_count } = data
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
           onClick={e => e.stopPropagation()}>
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-bold text-lg text-slate-800">{b.name}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">✕</button>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              ['المعرّف', b.id], ['رقم الهوية', b.national_id],
              ['الجوال', b.phone], ['المدينة', `${b.city} — ${b.district}`],
              ['حجم الأسرة', b.family_size], ['الدخل الشهري', `${b.monthly_income.toLocaleString('ar-SA')} ﷼`],
              ['تاريخ التسجيل', `${b.registration_date}م | ${b.registration_date_h}`],
              ['مصرف الزكاة', b.zakat_category ?? '—'],
            ].map(([label, val]) => (
              <div key={label as string} className="bg-slate-50 rounded-xl p-3">
                <p className="text-slate-400 text-xs mb-0.5">{label}</p>
                <p className="font-medium text-slate-700">{val}</p>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-primary-50 rounded-xl p-3">
              <p className="text-slate-400 text-xs mb-0.5">إجمالي الطلبات</p>
              <p className="font-bold text-primary-700 text-xl">{applications.length}</p>
            </div>
            <div className="bg-green-50 rounded-xl p-3">
              <p className="text-slate-400 text-xs mb-0.5">إجمالي ما صُرف</p>
              <p className="font-bold text-green-700 text-xl">{total_disbursed.toLocaleString('ar-SA')} ﷼</p>
            </div>
          </div>
          {applications.length > 0 && (
            <div>
              <h4 className="font-semibold text-slate-700 mb-2 text-sm">الطلبات ({applications.length})</h4>
              <div className="space-y-1">
                {applications.map((a: any) => (
                  <div key={a.id} className="flex items-center justify-between text-xs bg-slate-50 rounded-lg p-2">
                    <span className="text-slate-500">{a.id}</span>
                    <span className="font-medium">{a.sector}</span>
                    <span>{a.requested_amount.toLocaleString('ar-SA')} ﷼</span>
                    <span className="badge-blue">{a.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const EMPTY_FORM = {
  name: '', national_id: '', phone: '', city: 'الرياض', district: '',
  family_size: 4, monthly_income: 0, is_employed: false, has_disability: false,
}

export default function Beneficiaries() {
  const [list,    setList]    = useState<any[]>([])
  const [search,  setSearch]  = useState('')
  const [archived, setArchived] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [form,    setForm]    = useState({ ...EMPTY_FORM })
  const [saving,  setSaving]  = useState(false)
  const [result,  setResult]  = useState<any>(null)
  const [detailId, setDetailId] = useState<string | null>(null)
  const [editId,   setEditId]   = useState<string | null>(null)
  const [editForm, setEditForm] = useState<any>({})
  const [editSaving, setEditSaving] = useState(false)
  const [editMsg,  setEditMsg]  = useState('')
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    getBeneficiaries(search, archived).then(setList).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [search, archived])

  const handleSubmit = async (e: any) => {
    e.preventDefault()
    setSaving(true)
    try {
      const res = await createBeneficiary(form)
      setResult(res)
      setForm({ ...EMPTY_FORM })
      load()
    } catch (err: any) {
      setResult({ error: err.response?.data?.detail ?? 'حدث خطأ' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">المستفيدون</h1>
        <button onClick={() => { setShowForm(true); setResult(null) }} className="btn-primary flex items-center gap-2">
          <UserPlus size={16} /> تسجيل مستفيد جديد
        </button>
      </div>

      {/* Filters */}
      <div className="card flex items-center gap-4 flex-wrap">
        <div className="flex-1 min-w-[200px] relative">
          <Search size={15} className="absolute top-2.5 right-3 text-slate-400" />
          <input
            className="input pr-9"
            placeholder="بحث بالاسم أو رقم الهوية…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
          <input type="checkbox" checked={archived} onChange={e => setArchived(e.target.checked)} className="rounded" />
          إظهار المؤرشفين
        </label>
        <span className="text-xs text-slate-400 bg-slate-100 px-3 py-1.5 rounded-full">
          {list.length} مستفيد
        </span>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-slate-500 text-xs">
              <th className="px-5 py-3 text-right font-medium">الاسم</th>
              <th className="px-4 py-3 text-right font-medium">رقم الهوية</th>
              <th className="px-4 py-3 text-right font-medium">المدينة</th>
              <th className="px-4 py-3 text-right font-medium">الدخل ﷼</th>
              <th className="px-4 py-3 text-right font-medium">الأسرة</th>
              <th className="px-4 py-3 text-right font-medium">الأهلية</th>
              <th className="px-4 py-3 text-right font-medium">التسجيل</th>
              <th className="px-4 py-3 text-right font-medium">إجراء</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={8} className="text-center py-10 text-slate-400">جارٍ التحميل…</td></tr>
            )}
            {!loading && list.length === 0 && (
              <tr><td colSpan={8} className="text-center py-10 text-slate-400">لا يوجد مستفيدون</td></tr>
            )}
            {list.map(b => (
              <tr key={b.id} className={`border-b border-slate-50 hover:bg-slate-50 transition-colors
                ${b.is_archived ? 'opacity-50' : ''}`}>
                <td className="px-5 py-3">
                  <p className="font-medium text-slate-800">{b.name}</p>
                  <p className="text-xs text-slate-400">{b.id}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{b.national_id}</td>
                <td className="px-4 py-3 text-slate-600">{b.city}</td>
                <td className="px-4 py-3 text-slate-600">{b.monthly_income.toLocaleString('ar-SA')}</td>
                <td className="px-4 py-3 text-slate-600">{b.family_size}</td>
                <td className="px-4 py-3"><Badge eligible={b.is_eligible} /></td>
                <td className="px-4 py-3">
                  <p className="text-xs text-slate-600">{b.registration_date}</p>
                  <p className="text-xs text-slate-400">{b.registration_date_h}</p>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button onClick={() => setDetailId(b.id)}
                      className="p-1.5 rounded-lg hover:bg-blue-50 text-blue-500" title="عرض الملف">
                      <Eye size={14} />
                    </button>
                    <button onClick={() => {
                        setEditId(b.id)
                        setEditForm({ name: b.name, phone: b.phone, national_id: b.national_id,
                          city: b.city, district: b.district, family_size: b.family_size,
                          monthly_income: b.monthly_income, has_disability: b.has_disability })
                        setEditMsg('')
                      }}
                      className="p-1.5 rounded-lg hover:bg-violet-50 text-violet-500" title="تعديل">
                      <Pencil size={14} />
                    </button>
                    {!b.is_archived ? (
                      <button onClick={() => archiveBeneficiary(b.id).then(load)}
                        className="p-1.5 rounded-lg hover:bg-red-50 text-red-400" title="أرشفة">
                        <Archive size={14} />
                      </button>
                    ) : (
                      <button onClick={() => restoreBeneficiary(b.id).then(load)}
                        className="p-1.5 rounded-lg hover:bg-green-50 text-green-500" title="استعادة">
                        <RotateCcw size={14} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* New beneficiary modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
             onClick={() => setShowForm(false)}>
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
               onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-bold text-lg">تسجيل مستفيد جديد</h3>
              <button onClick={() => setShowForm(false)} className="text-slate-400">✕</button>
            </div>
            {result ? (
              <div className="p-6 text-center space-y-4">
                {result.error ? (
                  <div>
                    <p className="text-red-500 font-semibold">{result.error}</p>
                    <button onClick={() => setResult(null)} className="btn-secondary mt-3">رجوع</button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className={`text-xl font-bold ${result.is_eligible ? 'text-green-600' : 'text-amber-500'}`}>
                      {result.is_eligible ? '✓ تم التسجيل بنجاح — مؤهل' : '⚠ تم التسجيل — غير مؤهل حالياً'}
                    </p>
                    <p className="text-sm text-slate-500">{result.reason}</p>
                    <p className="text-xs text-slate-400">{result.beneficiary?.id}</p>
                    <p className="text-xs text-slate-400">
                      📅 {result.beneficiary?.registration_date}م | {result.beneficiary?.registration_date_h}
                    </p>
                    <button onClick={() => { setShowForm(false); setResult(null) }} className="btn-primary mt-2">إغلاق</button>
                  </div>
                )}
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="col-span-2">
                    <label className="text-xs text-slate-500 mb-1 block">الاسم الكامل *</label>
                    <input required className="input" value={form.name}
                      onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">رقم الهوية *</label>
                    <input required className="input" value={form.national_id}
                      onChange={e => setForm(f => ({ ...f, national_id: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">الجوال *</label>
                    <input required className="input" value={form.phone}
                      onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">المدينة</label>
                    <input className="input" value={form.city}
                      onChange={e => setForm(f => ({ ...f, city: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">الحي</label>
                    <input className="input" value={form.district}
                      onChange={e => setForm(f => ({ ...f, district: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">حجم الأسرة</label>
                    <input type="number" min={1} className="input" value={form.family_size}
                      onChange={e => setForm(f => ({ ...f, family_size: +e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">الدخل الشهري (ريال)</label>
                    <input type="number" min={0} step={100} className="input" value={form.monthly_income}
                      onChange={e => setForm(f => ({ ...f, monthly_income: +e.target.value }))} />
                  </div>
                  <label className="flex items-center gap-2 text-sm col-span-2 cursor-pointer">
                    <input type="checkbox" checked={form.is_employed}
                      onChange={e => setForm(f => ({ ...f, is_employed: e.target.checked }))} />
                    موظف بدخل مستقر
                  </label>
                  <label className="flex items-center gap-2 text-sm col-span-2 cursor-pointer">
                    <input type="checkbox" checked={form.has_disability}
                      onChange={e => setForm(f => ({ ...f, has_disability: e.target.checked }))} />
                    يعاني من إعاقة
                  </label>
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="submit" disabled={saving} className="btn-primary flex-1">
                    {saving ? 'جارٍ التسجيل…' : 'تسجيل المستفيد'}
                  </button>
                  <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">إلغاء</button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {detailId && <DetailModal id={detailId} onClose={() => setDetailId(null)} />}

      {/* Edit Modal */}
      {editId && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
             onClick={() => setEditId(null)}>
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
               onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-bold text-lg">✏️ تعديل بيانات المستفيد</h3>
              <button onClick={() => setEditId(null)} className="text-slate-400">✕</button>
            </div>
            <div className="p-6 space-y-4">
              {editMsg && (
                <div className={`text-sm p-3 rounded-lg ${editMsg.startsWith('✓') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                  {editMsg}
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2">
                  <label className="text-xs text-slate-500 block mb-1">الاسم الكامل</label>
                  <input className="input" value={editForm.name ?? ''}
                    onChange={e => setEditForm((f: any) => ({ ...f, name: e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">الجوال</label>
                  <input className="input" value={editForm.phone ?? ''}
                    onChange={e => setEditForm((f: any) => ({ ...f, phone: e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">رقم الهوية</label>
                  <input className="input" value={editForm.national_id ?? ''}
                    onChange={e => setEditForm((f: any) => ({ ...f, national_id: e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">المدينة</label>
                  <input className="input" value={editForm.city ?? ''}
                    onChange={e => setEditForm((f: any) => ({ ...f, city: e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">الحي</label>
                  <input className="input" value={editForm.district ?? ''}
                    onChange={e => setEditForm((f: any) => ({ ...f, district: e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">حجم الأسرة</label>
                  <input type="number" min={1} className="input" value={editForm.family_size ?? 1}
                    onChange={e => setEditForm((f: any) => ({ ...f, family_size: +e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">الدخل الشهري (ريال)</label>
                  <input type="number" min={0} step={100} className="input" value={editForm.monthly_income ?? 0}
                    onChange={e => setEditForm((f: any) => ({ ...f, monthly_income: +e.target.value }))} />
                </div>
                <label className="flex items-center gap-2 text-sm col-span-2 cursor-pointer">
                  <input type="checkbox" checked={editForm.has_disability ?? false}
                    onChange={e => setEditForm((f: any) => ({ ...f, has_disability: e.target.checked }))} />
                  يعاني من إعاقة
                </label>
              </div>
              <div className="flex gap-3 pt-2">
                <button disabled={editSaving} className="btn-primary flex-1"
                  onClick={async () => {
                    setEditSaving(true); setEditMsg('')
                    try {
                      const res = await updateBeneficiary(editId!, editForm)
                      setEditMsg(`✓ تم التحديث — الأهلية: ${res.is_eligible ? 'مؤهل' : 'غير مؤهل'}`)
                      load()
                    } catch (err: any) {
                      setEditMsg(`✗ ${err.response?.data?.detail ?? 'حدث خطأ'}`)
                    } finally { setEditSaving(false) }
                  }}>
                  {editSaving ? 'جارٍ الحفظ…' : 'حفظ التعديلات'}
                </button>
                <button onClick={() => setEditId(null)} className="btn-secondary">إغلاق</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
