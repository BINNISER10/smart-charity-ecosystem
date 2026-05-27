import { useState, useEffect } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard, Users, FileText, Wallet, BarChart3,
  Star, Shield, Bell, Menu, X, Save, BookOpen, Heart
} from 'lucide-react'
import { todayHijri, saveData } from '../lib/api'

const nav = [
  { to: '/',           icon: LayoutDashboard, label: 'لوحة التحكم'   },
  { to: '/beneficiaries', icon: Users,        label: 'المستفيدون'    },
  { to: '/applications',  icon: FileText,     label: 'الطلبات'       },
  { to: '/finance',       icon: Wallet,       label: 'المالية'       },
  { to: '/sectors',       icon: BarChart3,    label: 'القطاعات'      },
  { to: '/zakat',         icon: Star,         label: 'حاسبة الزكاة'  },
  { to: '/audit',         icon: Shield,       label: 'سجل التدقيق'   },
  { to: '/alerts',        icon: Bell,         label: 'التنبيهات'     },
  { to: '/config',        icon: BookOpen,     label: 'القواعد والهيكل'},
  { to: '/donors',        icon: Heart,        label: 'المتبرعون'     },
]

export default function Layout() {
  const [open,    setOpen]    = useState(true)
  const [dualDate, setDualDate] = useState('')
  const [saving,  setSaving]  = useState(false)
  const [saved,   setSaved]   = useState(false)

  useEffect(() => {
    todayHijri().then(d => setDualDate(d.dual)).catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try { await saveData(); setSaved(true); setTimeout(() => setSaved(false), 2000) }
    finally { setSaving(false) }
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Sidebar */}
      <aside className={`
        fixed top-0 right-0 h-full z-30 bg-white border-l border-slate-200
        flex flex-col transition-all duration-300 shadow-lg
        ${open ? 'w-60' : 'w-16'}
      `}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-slate-100">
          <div className="w-9 h-9 rounded-xl bg-primary-600 flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-lg">خ</span>
          </div>
          {open && (
            <div className="overflow-hidden">
              <p className="font-bold text-slate-800 text-sm leading-tight">منظومة الخير</p>
              <p className="text-xs text-slate-400">الذكاء الخيري</p>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 overflow-y-auto">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 mx-2 rounded-xl mb-1 text-sm font-medium transition-all
                 ${isActive
                   ? 'bg-primary-600 text-white shadow-sm'
                   : 'text-slate-600 hover:bg-slate-100'}`
              }
            >
              <Icon size={18} className="flex-shrink-0" />
              {open && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Save button */}
        <div className="p-3 border-t border-slate-100">
          <button
            onClick={handleSave}
            disabled={saving}
            className={`
              flex items-center gap-2 w-full px-3 py-2 rounded-xl text-sm font-medium transition-all
              ${saved
                ? 'bg-green-100 text-green-700'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-600'}
            `}
          >
            <Save size={16} />
            {open && <span>{saving ? 'جارٍ الحفظ…' : saved ? 'تم الحفظ ✓' : 'حفظ البيانات'}</span>}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ${open ? 'mr-60' : 'mr-16'}`}>
        {/* Top bar */}
        <header className="sticky top-0 z-20 bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
          <button
            onClick={() => setOpen(!open)}
            className="p-2 rounded-lg hover:bg-slate-100 text-slate-500"
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>

          <div className="flex items-center gap-3">
            {dualDate && (
              <span className="text-xs text-slate-500 bg-slate-50 px-3 py-1.5 rounded-full border border-slate-200">
                📅 {dualDate}
              </span>
            )}
          </div>
        </header>

        {/* Page */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
