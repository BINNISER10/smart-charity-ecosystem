"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Loader2, LogIn, Heart, Users, BarChart3, Sparkles } from "lucide-react";
import toast from "react-hot-toast";
import { authApi } from "@/lib/api";
import { saveSession, redirectAfterLogin } from "@/lib/auth";

const FEATURES = [
  { icon: Users,      text: "إدارة المستفيدين بذكاء اصطناعي" },
  { icon: BarChart3,  text: "لوحة تحكم تحليلية متكاملة" },
  { icon: Sparkles,   text: "Fast-Track تلقائي للحالات الحرجة" },
  { icon: Heart,      text: "تقارير الأثر للمتبرعين" },
];

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: "", password: "", tenant_id: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.username || !form.password || !form.tenant_id) {
      toast.error("يرجى ملء جميع الحقول");
      return;
    }
    setLoading(true);
    try {
      const data = await authApi.login(form);
      saveSession(data.access_token, data.role, data.tenant_id);
      toast.success(`مرحباً! دخلت كـ ${data.role}`);
      router.push(redirectAfterLogin(data.role));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "فشل تسجيل الدخول";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const inp = "w-full rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-900 placeholder:text-gray-400 focus:border-brand-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition";
  const lbl = "block text-sm font-semibold text-gray-700 mb-2";

  return (
    <div className="min-h-screen flex" dir="rtl">
      {/* ── الجانب الأيمن: التدرج الأزرق ── */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-brand-800 via-brand-700 to-brand-900 flex-col justify-between p-12 relative overflow-hidden">
        {/* خلفية زخرفية */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-20 -right-20 w-72 h-72 rounded-full bg-white/5 blur-3xl" />
          <div className="absolute bottom-20 -left-10 w-96 h-96 rounded-full bg-brand-950/40 blur-3xl" />
        </div>

        {/* الشعار */}
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
              <Heart className="h-6 w-6 text-white" />
            </div>
            <div>
              <p className="text-white font-bold text-lg leading-tight">منظومة العمل الخيري</p>
              <p className="text-brand-200 text-xs">Smart Charity Ecosystem</p>
            </div>
          </div>
        </div>

        {/* العنوان الرئيسي */}
        <div className="relative z-10">
          <h1 className="text-4xl font-extrabold text-white leading-snug mb-4">
            منصة خيرية<br />
            <span className="text-brand-200">ذكية ومتكاملة</span>
          </h1>
          <p className="text-brand-200 text-base leading-relaxed mb-10">
            نظام SaaS متعدد المستأجرين لإدارة المستفيدين والطلبات والتبرعات بقوة الذكاء الاصطناعي
          </p>

          {/* المميزات */}
          <div className="space-y-3">
            {FEATURES.map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10">
                  <Icon className="h-4 w-4 text-brand-200" />
                </div>
                <span className="text-brand-100 text-sm">{text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* الذيل */}
        <div className="relative z-10">
          <p className="text-brand-300 text-xs">© 2026 Smart Charity Ecosystem — جميع الحقوق محفوظة</p>
        </div>
      </div>

      {/* ── الجانب الأيسر: نموذج الدخول ── */}
      <div className="flex-1 flex items-center justify-center bg-white p-8">
        <div className="w-full max-w-md">
          {/* شعار موبايل */}
          <div className="flex lg:hidden items-center gap-3 mb-8 justify-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600">
              <Heart className="h-5 w-5 text-white" />
            </div>
            <p className="text-gray-900 font-bold text-lg">منظومة العمل الخيري</p>
          </div>

          {/* العنوان */}
          <div className="mb-8">
            <h2 className="text-2xl font-extrabold text-gray-900 mb-1">مرحباً بك 👋</h2>
            <p className="text-gray-500 text-sm">سجّل دخولك للوصول إلى لوحة التحكم</p>
          </div>

          {/* النموذج */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className={lbl}>معرّف المؤسسة</label>
              <input
                type="text" className={inp} placeholder="org_a" dir="ltr"
                value={form.tenant_id}
                onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
              />
            </div>
            <div>
              <label className={lbl}>اسم المستخدم</label>
              <input
                type="text" className={inp} placeholder="admin@org_a" dir="ltr"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
              />
            </div>
            <div>
              <label className={lbl}>كلمة المرور</label>
              <input
                type="password" className={inp} placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-brand-600 py-3.5 text-sm font-bold text-white shadow-lg shadow-brand-600/30 hover:bg-brand-700 transition disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <LogIn className="h-4 w-4" />}
              {loading ? "جارٍ الدخول…" : "تسجيل الدخول"}
            </button>
          </form>

          {/* بيانات تجريبية */}
          <div className="mt-6 rounded-2xl bg-brand-50 border border-brand-100 p-4">
            <p className="text-xs font-bold text-brand-700 mb-2 flex items-center gap-1">
              <Sparkles className="h-3 w-3" /> بيانات تجريبية
            </p>
            <div className="space-y-1 text-xs text-brand-600 font-mono">
              <p>admin@org_a / admin123 / <span className="font-bold">org_a</span></p>
              <p>field@org_a / field789 / <span className="font-bold">org_a</span></p>
              <p>admin@org_b / admin123 / <span className="font-bold">org_b</span></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
