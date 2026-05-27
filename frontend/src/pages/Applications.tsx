import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Trash2, Banknote, PlusCircle, Pencil } from 'lucide-react'
import {
  getApplications, approveApplication, rejectApplication,
  cancelApplication, disburseApplication, createApplication,
  getBeneficiaries, getEnums, getUsers, updateApplication
} from '../lib/api'

const STATUS_BADGE: Record<string, string> = {
  'مسودة':                'badge-gray',
  'مقدَّم':               'badge-blue',
  'تم التحليل الذكي':     'badge-yellow',
  'بانتظار الموافقة':     'badge-yellow',
  'موافق عليه':           'badge-green',
  'مرفوض':               'badge-red',
  'تم الصرف':            'badge-green',
  'ملغى':                'badge-gray',
  'مغلق':                'badge-gray',
}

const PRIORITY_BADGE: Record<string, string> = {
  CRITICAL: 'badge-red',
  HIGH:     'badge-yellow',
  MEDIUM:   'badge-blue',
  LOW:      'badge-gray',
}

export default function Applications() {
  const [list,    setList]    = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter,  setFilter]  = useState({ status: '', sector: '' })
  const [selected, setSelected] = useState<any>(null)
  const [actionData, setActionData] = useState<any>({})
  const [showNew,  setShowNew]  = useState(false)
  const [bens,     setBens]     = useState<any[]>([])
  const [enums,    setEnums]    = useState<any>({})
  const [users,    setUsers]    = useState<any[]>([])
  const [newForm,  setNewForm]  = useState<any>({
    beneficiary_id: '', sector: '', fund_type: '', requested_amount: '', description: '', supporting_docs: ''
  })
  const [submitting, setSubmitting] = useState(false)
  const [newResult,  setNewResult]  = useState<any>(null)

  const load = () => {
    setLoading(true)
    getApplications(filter).then(setList).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filter])
  useEffect(() => {
    getBeneficiaries('', false).then(b => setBens(b.filter((x: any) => x.is_eligible)))
    getEnums().then(setEnums)
    getUsers().then(setUsers)
  }, [])

  const doAction = async (type: string) => {
    if (!selected) return
    try {
      if (type === 'approve')
        await approveApplication(selected.id, {
          approver_id:     actionData.approver_id || 'API-ADMIN',
          approved_amount: Number(actionData.approved_amount),
          notes:           actionData.notes || '',
        })
      else if (type === 'reject')
        await rejectApplication(selected.id, { rejector_id: 'API', reason: actionData.reason || 'مرفوض' })
      else if (type === 'cancel')
        await cancelApplication(selected.id, { canceller_id: 'API', reason: actionData.reason || '' })
      else if (type === 'disburse')
        await disburseApplication(selected.id)
      setSelected(null); setActionData({})
      load()
    } catch (err: any) {
      alert(err.response?.data?.detail ?? 'فشل الإجراء')
    }
  }

  const handleNew = async (e: any) => {
    e.preventDefault(); setSubmitting(true)
    try {
      const res = await createApplication({
        ...newForm,
        requested_amount: Number(newForm.requested_amount),
        supporting_docs:  newForm.supporting_docs.split('،').map((s: string) => s.trim()).filter(Boolean),
      })
      setNewResult(res)
      load()
    } catch (err: any) {
      setNewResult({ error: err.response?.data?.detail ?? 'حدث خطأ' })
    } finally { setSubmitting(false) }
  }

  const canApprove  = (s: string) => ['مقدَّم','تم التحليل الذكي','بانتظار الموافقة'].includes(s)
  const canReject   = (s: string) => canApprove(s)
  const canCancel   = (s: string) => !['تم الصرف','ملغى','مغلق'].includes(s)
  const canDisburse = (s: string) => s === 'موافق عليه'
  const canEdit     = (s: string) => ['مسودة','مقدَّم','تم التحليل الذكي'].includes(s)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">الطلبات</h1>
        <button onClick={() => { setShowNew(true); setNewResult(null) }} className="btn-primary flex items-center gap-2">
          <PlusCircle size={16} /> طلب جديد
        </button>
      </div>

      {/* Filters */}
      <div className="card flex flex-wrap gap-4 items-center">
        <div>
          <label className="text-xs text-slate-500 block mb-1">الحالة</label>
          <select className="input w-48"
            value={filter.status}
            onChange={e => setFilter(f => ({ ...f, status: e.target.value }))}>
            <option value="">الكل</option>
            {enums.app_statuses?.map((s: string) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-500 block mb-1">القطاع</label>
          <select className="input w-48"
            value={filter.sector}
            onChange={e => setFilter(f => ({ ...f, sector: e.target.value }))}>
            <option value="">الكل</option>
            {enums.sector_types?.map((s: string) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <span className="text-xs text-slate-400 bg-slate-100 px-3 py-1.5 rounded-full self-end">
          {list.length} طلب
        </span>
      </div>

      {/* Table */}
      <div className="card overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-slate-500 text-xs">
              <th className="px-5 py-3 text-right font-medium">المعرّف</th>
              <th className="px-4 py-3 text-right font-medium">القطاع</th>
              <th className="px-4 py-3 text-right font-medium">الصندوق</th>
              <th className="px-4 py-3 text-right font-medium">المطلوب ﷼</th>
              <th className="px-4 py-3 text-right font-medium">المعتمد ﷼</th>
              <th className="px-4 py-3 text-right font-medium">الأولوية</th>
              <th className="px-4 py-3 text-right font-medium">الحالة</th>
              <th className="px-4 py-3 text-right font-medium">التاريخ</th>
              <th className="px-4 py-3 text-right font-medium">إجراء</th>
            </tr>
          </thead>
          <tbody>
            {loading && <tr><td colSpan={9} className="text-center py-10 text-slate-400">جارٍ التحميل…</td></tr>}
            {!loading && list.length === 0 && <tr><td colSpan={9} className="text-center py-10 text-slate-400">لا توجد طلبات</td></tr>}
            {list.map(a => (
              <tr key={a.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                <td className="px-5 py-3">
                  <p className="font-medium text-slate-800 text-xs">{a.id}</p>
                  <p className="text-xs text-slate-400 truncate max-w-[140px]">{a.description}</p>
                </td>
                <td className="px-4 py-3 text-slate-600">{a.sector}</td>
                <td className="px-4 py-3 text-slate-600">{a.fund_type}</td>
                <td className="px-4 py-3 font-medium text-slate-700">{a.requested_amount.toLocaleString('ar-SA')}</td>
                <td className="px-4 py-3 font-medium text-green-600">
                  {a.approved_amount > 0 ? a.approved_amount.toLocaleString('ar-SA') : '—'}
                </td>
                <td className="px-4 py-3">
                  <span className={PRIORITY_BADGE[a.priority] ?? 'badge-gray'}>{a.priority}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={STATUS_BADGE[a.status] ?? 'badge-gray'}>{a.status}</span>
                </td>
                <td className="px-4 py-3">
                  <p className="text-xs text-slate-600">{a.submission_date}</p>
                  <p className="text-xs text-slate-400">{a.submission_date_h}</p>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1.5">
                    {canApprove(a.status) && (
                      <button onClick={() => { setSelected(a); setActionData({ approved_amount: a.requested_amount }) }}
                        className="p-1.5 rounded-lg bg-green-50 hover:bg-green-100 text-green-600" title="موافقة">
                        <CheckCircle size={14} />
                      </button>
                    )}
                    {canReject(a.status) && (
                      <button onClick={() => { setSelected({ ...a, _action: 'reject' }); setActionData({}) }}
                        className="p-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-500" title="رفض">
                        <XCircle size={14} />
                      </button>
                    )}
                    {canCancel(a.status) && (
                      <button onClick={() => { setSelected({ ...a, _action: 'cancel' }); setActionData({}) }}
                        className="p-1.5 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-500" title="إلغاء">
                        <Trash2 size={14} />
                      </button>
                    )}
                    {canDisburse(a.status) && (
                      <button onClick={() => setSelected({ ...a, _action: 'disburse' })}
                        className="p-1.5 rounded-lg bg-violet-50 hover:bg-violet-100 text-violet-600" title="صرف">
                        <Banknote size={14} />
                      </button>
                    )}
                    {canEdit(a.status) && (
                      <button onClick={() => setSelected({ ...a, _action: 'edit' })
                        }
                        className="p-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-600" title="تعديل">
                        <Pencil size={14} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Action Modal */}
      {selected && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
             onClick={() => setSelected(null)}>
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-6 space-y-4"
               onClick={e => e.stopPropagation()}>
            {selected._action === 'edit' ? (
              <>
                <h3 className="font-bold text-lg">✏️ تعديل الطلب</h3>
                <p className="text-xs text-slate-400">{selected.id}</p>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">وصف الحاجة</label>
                    <textarea rows={3} className="input resize-none"
                      value={actionData.description ?? selected.description}
                      onChange={e => setActionData((d: any) => ({ ...d, description: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">المبلغ المطلوب (ريال)</label>
                    <input type="number" min={1} className="input"
                      value={actionData.requested_amount ?? selected.requested_amount}
                      onChange={e => setActionData((d: any) => ({ ...d, requested_amount: +e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">الأولوية</label>
                    <select className="input"
                      value={actionData.priority ?? selected.priority}
                      onChange={e => setActionData((d: any) => ({ ...d, priority: e.target.value }))}>
                      {['CRITICAL','HIGH','MEDIUM','LOW'].map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button className="btn-primary flex-1" onClick={async () => {
                    try {
                      await updateApplication(selected.id, {
                        description:      actionData.description ?? selected.description,
                        requested_amount: actionData.requested_amount ?? selected.requested_amount,
                        priority:         actionData.priority ?? selected.priority,
                      })
                      setSelected(null); setActionData({}); load()
                    } catch (err: any) { alert(err.response?.data?.detail ?? 'فشل التعديل') }
                  }}>حفظ التعديلات</button>
                  <button onClick={() => setSelected(null)} className="btn-secondary">إلغاء</button>
                </div>
              </>
            ) : selected._action === 'disburse' ? (
              <>
                <h3 className="font-bold text-lg">تأكيد الصرف</h3>
                <p className="text-slate-600 text-sm">هل تريد صرف <strong>{selected.approved_amount?.toLocaleString('ar-SA')} ريال</strong> للطلب <strong>{selected.id}</strong>؟</p>
                <div className="flex gap-3">
                  <button onClick={() => doAction('disburse')} className="btn-primary flex-1">تأكيد الصرف</button>
                  <button onClick={() => setSelected(null)} className="btn-secondary">إلغاء</button>
                </div>
              </>
            ) : selected._action === 'reject' || selected._action === 'cancel' ? (
              <>
                <h3 className="font-bold text-lg">{selected._action === 'reject' ? 'رفض الطلب' : 'إلغاء الطلب'}</h3>
                <label className="text-xs text-slate-500 block">السبب</label>
                <input className="input" placeholder="اكتب السبب…"
                  value={actionData.reason ?? ''}
                  onChange={e => setActionData((d: any) => ({ ...d, reason: e.target.value }))} />
                <div className="flex gap-3">
                  <button onClick={() => doAction(selected._action)}
                    className="btn-danger flex-1">تأكيد</button>
                  <button onClick={() => setSelected(null)} className="btn-secondary">إلغاء</button>
                </div>
              </>
            ) : (
              <>
                <h3 className="font-bold text-lg">موافقة على الطلب</h3>
                <p className="text-xs text-slate-500">{selected.id} — {selected.sector}</p>
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">المبلغ المعتمد (ريال)</label>
                    <input type="number" className="input"
                      value={actionData.approved_amount ?? selected.requested_amount}
                      onChange={e => setActionData((d: any) => ({ ...d, approved_amount: e.target.value }))} />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">الموافق</label>
                    <select className="input"
                      value={actionData.approver_id ?? 'API-ADMIN'}
                      onChange={e => setActionData((d: any) => ({ ...d, approver_id: e.target.value }))}>
                      {users.filter(u => u.is_active).map(u => (
                        <option key={u.user_id} value={u.user_id}>
                          {u.name} — {u.role}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">ملاحظات</label>
                    <input className="input" placeholder="اختياري…"
                      value={actionData.notes ?? ''}
                      onChange={e => setActionData((d: any) => ({ ...d, notes: e.target.value }))} />
                  </div>
                </div>
                <div className="flex gap-3">
                  <button onClick={() => doAction('approve')} className="btn-primary flex-1">تأكيد الموافقة</button>
                  <button onClick={() => setSelected(null)} className="btn-secondary">إلغاء</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* New Application Modal */}
      {showNew && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
             onClick={() => setShowNew(false)}>
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
               onClick={e => e.stopPropagation()}>
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-bold text-lg">تقديم طلب جديد</h3>
              <button onClick={() => setShowNew(false)} className="text-slate-400">✕</button>
            </div>
            {newResult ? (
              <div className="p-6 text-center space-y-3">
                {newResult.error
                  ? <><p className="text-red-500 font-semibold">{newResult.error}</p>
                      <button onClick={() => setNewResult(null)} className="btn-secondary">رجوع</button></>
                  : <><p className="text-green-600 font-bold text-lg">✓ تم تقديم الطلب بنجاح</p>
                      <p className="text-sm text-slate-500">{newResult.application?.id}</p>
                      <p className="text-sm">نقاط الذكاء: <strong>{newResult.application?.ai_score?.toFixed(1)}</strong></p>
                      <p className="text-xs text-slate-400">{newResult.application?.ai_recommendation}</p>
                      <button onClick={() => { setShowNew(false); setNewResult(null) }} className="btn-primary mt-2">إغلاق</button></>
                }
              </div>
            ) : (
              <form onSubmit={handleNew} className="p-6 space-y-4">
                <div>
                  <label className="text-xs text-slate-500 block mb-1">المستفيد *</label>
                  <select required className="input"
                    value={newForm.beneficiary_id}
                    onChange={e => setNewForm((f: any) => ({ ...f, beneficiary_id: e.target.value }))}>
                    <option value="">اختر مستفيداً مؤهلاً…</option>
                    {bens.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">القطاع *</label>
                    <select required className="input"
                      value={newForm.sector}
                      onChange={e => setNewForm((f: any) => ({ ...f, sector: e.target.value }))}>
                      <option value="">اختر…</option>
                      {enums.sector_types?.map((s: string) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 block mb-1">الصندوق *</label>
                    <select required className="input"
                      value={newForm.fund_type}
                      onChange={e => setNewForm((f: any) => ({ ...f, fund_type: e.target.value }))}>
                      <option value="">اختر…</option>
                      {enums.fund_types?.map((s: string) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">المبلغ المطلوب (ريال) *</label>
                  <input required type="number" min={1} className="input"
                    value={newForm.requested_amount}
                    onChange={e => setNewForm((f: any) => ({ ...f, requested_amount: e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">وصف الحاجة *</label>
                  <textarea required rows={3} className="input resize-none"
                    value={newForm.description}
                    onChange={e => setNewForm((f: any) => ({ ...f, description: e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs text-slate-500 block mb-1">المستندات (افصل بـ ،)</label>
                  <input className="input" placeholder="تقرير طبي، فاتورة، ..."
                    value={newForm.supporting_docs}
                    onChange={e => setNewForm((f: any) => ({ ...f, supporting_docs: e.target.value }))} />
                </div>
                <div className="flex gap-3 pt-2">
                  <button type="submit" disabled={submitting} className="btn-primary flex-1">
                    {submitting ? 'جارٍ التقديم…' : 'تقديم الطلب'}
                  </button>
                  <button type="button" onClick={() => setShowNew(false)} className="btn-secondary">إلغاء</button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
