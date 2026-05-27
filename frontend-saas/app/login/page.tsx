"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Loader2, LogIn, Shield } from "lucide-react";
import toast from "react-hot-toast";
import { authApi } from "@/lib/api";
import { saveSession, redirectAfterLogin } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    username:  "",
    password:  "",
    tenant_id: "",
  });
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
      const msg =
        (err as { response?: { data?: { detail?: string } } })
          .response?.data?.detail ?? "فشل تسجيل الدخول";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-900 via-brand-800 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 backdrop-blur mb-4">
            <Shield className="w-8 h-8 text-brand-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">منظومة العمل الخيري</h1>
          <p className="text-brand-300 text-sm mt-1">نظام SaaS متعدد المستأجرين</p>
        </div>

        {/* Card */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 shadow-2xl">
          <h2 className="text-xl font-bold text-white mb-6">تسجيل الدخول</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                معرّف المؤسسة (Tenant ID)
              </label>
              <input
                type="text"
                placeholder="org_a"
                value={form.tenant_id}
                onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
                className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2.5 text-white placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/30 text-sm"
                dir="ltr"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                اسم المستخدم
              </label>
              <input
                type="email"
                placeholder="admin@org_a"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2.5 text-white placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/30 text-sm"
                dir="ltr"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                كلمة المرور
              </label>
              <input
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2.5 text-white placeholder:text-slate-400 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-400/30 text-sm"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-brand-600 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-brand-500 disabled:opacity-60 disabled:cursor-not-allowed mt-2"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <LogIn className="w-4 h-4" />
              )}
              {loading ? "جارٍ الدخول…" : "تسجيل الدخول"}
            </button>
          </form>

          {/* Demo hint */}
          <div className="mt-5 rounded-lg bg-white/5 border border-white/10 p-3 text-xs text-slate-400">
            <p className="font-medium text-slate-300 mb-1">بيانات تجريبية:</p>
            <p>admin@org_a / admin123 / org_a</p>
            <p>field@org_a / field789 / org_a</p>
          </div>
        </div>
      </div>
    </div>
  );
}
