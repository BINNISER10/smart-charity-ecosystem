import { useEffect, useState } from 'react'
import { Heart, Search, Users, TrendingUp, DollarSign, Calendar } from 'lucide-react'
import { getDonors } from '../lib/api'

interface Donor {
  donor_id: string
  full_name: string
  phone: string
  fund_type: string
  total_donated: number
  donation_count: number
  first_donation_date:   string | null
  first_donation_date_h: string | null
}

const FUND_COLORS: Record<string, string> = {
  'الزكاة':          'badge-green',
  'الصدقات':         'badge-blue',
  'الأوقاف':         'badge-yellow',
  'المشاريع المقيدة': 'badge-gray',
}

export default function Donors() {
  const [donors,  setDonors]  = useState<Donor[]>([])
  const [search,  setSearch]  = useState('')
  const [loading, setLoading] = useState(true)

  const load = (q = '') => {
    setLoading(true)
    getDonors(q)
      .then(setDonors)
      .catch(() => setDonors([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    load(search)
  }

  const totalDonated = donors.reduce((s, d) => s + d.total_donated, 0)
  const totalCount   = donors.reduce((s, d) => s + d.donation_count, 0)
  const topDonor: Donor | null = donors.length
    ? donors.reduce<Donor>((a, b) => a.total_donated > b.total_donated ? a : b, donors[0])
    : null

  const fundBreakdown: Record<string, number> = donors.reduce<Record<string, number>>((acc, d) => {
    acc[d.fund_type] = (acc[d.fund_type] ?? 0) + d.total_donated
    return acc
  }, {})

  const formatDate = (d: string | null) => d ?? '—'

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-rose-100 flex items-center justify-center">
          <Heart size={20} className="text-rose-600" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-800">المتبرعون</h1>
          <p className="text-sm text-slate-500">سجل التبرعات وبيانات المتبرعين</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-rose-100 flex items-center justify-center">
              <Users size={16} className="text-rose-600" />
            </div>
            <div>
              <p className="text-xs text-slate-500">إجمالي المتبرعين</p>
              <p className="text-xl font-bold text-slate-800">{donors.length}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-green-100 flex items-center justify-center">
              <DollarSign size={16} className="text-green-600" />
            </div>
            <div>
              <p className="text-xs text-slate-500">إجمالي التبرعات</p>
              <p className="text-xl font-bold text-slate-800">{totalDonated.toLocaleString('ar-SA')} ر</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center">
              <TrendingUp size={16} className="text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-slate-500">عدد العمليات</p>
              <p className="text-xl font-bold text-slate-800">{totalCount}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-100 flex items-center justify-center">
              <Heart size={16} className="text-amber-600" />
            </div>
            <div>
              <p className="text-xs text-slate-500">أكبر متبرع</p>
              <p className="text-sm font-bold text-slate-800 truncate">
                {topDonor ? topDonor.full_name : '—'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Fund Breakdown */}
      {Object.keys(fundBreakdown).length > 0 && (
        <div className="card">
          <h2 className="font-semibold text-slate-700 mb-3">توزيع التبرعات على الصناديق</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(fundBreakdown).map(([fund, amount]) => (
              <div key={fund} className="bg-slate-50 rounded-xl p-3 text-center">
                <p className="text-xs text-slate-500 mb-1">{fund}</p>
                <p className="font-bold text-slate-800">{amount.toLocaleString('ar-SA')} ر</p>
                <div className="mt-1.5">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                    ${FUND_COLORS[fund] === 'badge-green'  ? 'bg-green-100 text-green-700'  : ''}
                    ${FUND_COLORS[fund] === 'badge-blue'   ? 'bg-blue-100 text-blue-700'    : ''}
                    ${FUND_COLORS[fund] === 'badge-yellow' ? 'bg-amber-100 text-amber-700'  : ''}
                    ${FUND_COLORS[fund] === 'badge-gray'   ? 'bg-slate-100 text-slate-600'  : ''}
                  `}>
                    {totalDonated > 0 ? ((amount / totalDonated) * 100).toFixed(1) : '0'}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="ابحث بالاسم أو الجوال…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input pr-9 w-full"
          />
        </div>
        <button type="submit" className="btn-primary px-5">بحث</button>
        {search && (
          <button
            type="button"
            onClick={() => { setSearch(''); load('') }}
            className="btn-secondary px-4"
          >
            مسح
          </button>
        )}
      </form>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-32 text-slate-400 text-sm">
            جارٍ التحميل…
          </div>
        ) : donors.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-slate-400 gap-2">
            <Heart size={28} className="opacity-30" />
            <p className="text-sm">لا توجد بيانات متبرعين</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500">#</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500">الاسم</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500">الجوال</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500">الصندوق</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500">إجمالي التبرعات</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500">عدد المرات</th>
                <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500">أول تبرع</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {donors.map((d, i) => (
                <tr key={d.donor_id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 text-slate-400 text-xs">{i + 1}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-rose-100 flex items-center justify-center flex-shrink-0">
                        <span className="text-rose-600 text-xs font-bold">{d.full_name.charAt(0)}</span>
                      </div>
                      <span className="font-medium text-slate-800">{d.full_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-600 font-mono text-xs">{d.phone}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded-full font-medium
                      ${d.fund_type === 'الزكاة'           ? 'bg-green-100 text-green-700'  : ''}
                      ${d.fund_type === 'الصدقات'          ? 'bg-blue-100 text-blue-700'    : ''}
                      ${d.fund_type === 'الأوقاف'          ? 'bg-amber-100 text-amber-700'  : ''}
                      ${d.fund_type === 'المشاريع المقيدة' ? 'bg-slate-100 text-slate-600'  : ''}
                    `}>
                      {d.fund_type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-bold text-green-700">
                    {d.total_donated.toLocaleString('ar-SA')} ر
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span className="badge-gray">{d.donation_count}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-500 text-xs">
                    <span className="flex flex-col gap-0.5">
                      <span className="flex items-center gap-1">
                        <Calendar size={11} />
                        {formatDate(d.first_donation_date)}
                      </span>
                      {d.first_donation_date_h && (
                        <span className="text-slate-400 text-xs">{d.first_donation_date_h}</span>
                      )}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

    </div>
  )
}
