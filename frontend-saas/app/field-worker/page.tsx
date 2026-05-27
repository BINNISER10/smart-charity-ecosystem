"use client";

import { useState, FormEvent } from "react";
import {
  User, Phone, MapPin, Users, DollarSign,
  FileText, Zap, CheckCircle2, Loader2, ChevronDown,
} from "lucide-react";
import toast from "react-hot-toast";
import { beneficiariesApi, applicationsApi, HolisticPlanResponse } from "@/lib/api";

// ── بيانات القطاعات والصناديق ─────────────────────────────────────────────────
const SECTORS   = ["الصحة", "التعليم", "السكن", "الغذاء"];
const FUND_TYPES = ["الزكاة", "الصدقات", "الأوقاف", "الكفارات"];

// ── حالة النموذج ──────────────────────────────────────────────────────────────
const EMPTY_BEN = {
  full_name:       "",
  national_id:     "",
  phone:           "",
  city:            "",
  district:        "",
  family_size:     1,
  monthly_income:  0,
  is_employed:     false,
  has_disability:  false,
  field_notes:     "",
};

const EMPTY_APP = {
  sector:           "الصحة",
  requested_amount: 0,
  fund_type:        "الزكاة",
  description:      "",
};

// ── مكوّن حقل الإدخال ─────────────────────────────────────────────────────────
function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  );
}

export default function FieldWorkerPage() {
  const [ben,      setBen]     = useState(EMPTY_BEN);
  const [app,      setApp]     = useState(EMPTY_APP);
  const [loading,  setLoading] = useState(false);
  const [step,     setStep]    = useState<"form" | "done">("form");
  const [result,   setResult]  = useState<{
    plan: HolisticPlanResponse;
    app: { fast_tracked: boolean; status: string; message: string; application_id: string };
  } | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    // التحقق الأساسي
    if (!ben.full_name || !ben.national_id || !ben.phone) {
      toast.error("يرجى ملء الاسم والهوية والهاتف على الأقل");
      return;
    }
    if (app.requested_amount <= 0) {
      toast.error("أدخل مبلغاً صالحاً");
      return;
    }

    setLoading(true);
    try {
      // الخطوة 1: تسجيل المستفيد + Holistic AI Triage
      const planData = await beneficiariesApi.create(ben);

      // الخطوة 2: تقديم الطلب (Fast-Track يعمل تلقائياً إذا تحققت الشروط)
      const appData = await applicationsApi.submit({
        beneficiary_id:   planData.beneficiary_id,
        sector:           app.sector,
        requested_amount: Number(app.requested_amount),
        fund_type:        app.fund_type,
        description:      app.description || `طلب ${app.sector} ميداني`,
      });

      setResult({ plan: planData, app: appData });
      setStep("done");

      if (appData.fast_tracked) {
        toast.success("⚡ مسار سريع! تم صرف الطلب فوراً", { duration: 6000 });
      } else {
        toast.success("تم تقديم الطلب بنجاح");
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })
          .response?.data?.detail ?? "حدث خطأ أثناء الإرسال";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setBen(EMPTY_BEN);
    setApp(EMPTY_APP);
    setResult(null);
    setStep("form");
  };

  // ── شاشة النجاح ──────────────────────────────────────────────────────────────
  if (step === "done" && result) {
    const { plan, app: appRes } = result;
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4">
        <div className="mx-auto max-w-md">
          <div className="card text-center">
            {appRes.fast_tracked ? (
              <>
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-100 dark:bg-amber-900/30">
                  <Zap className="h-8 w-8 text-amber-500" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">
                  مسار سريع ⚡
                </h2>
                <p className="text-sm text-slate-500 mb-4">
                  الطلب اعتُمد وصُرف تلقائياً في الحال!
                </p>
              </>
            ) : (
              <>
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-100 dark:bg-brand-900/30">
                  <CheckCircle2 className="h-8 w-8 text-brand-600" />
                </div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-1">
                  تم بنجاح
                </h2>
                <p className="text-sm text-slate-500 mb-4">
                  الطلب في طور المراجعة
                </p>
              </>
            )}

            <div className="rounded-xl bg-slate-50 dark:bg-slate-800 p-4 text-right space-y-2 mb-5">
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">المستفيد</span>
                <span className="font-medium">{ben.full_name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">الطلب</span>
                <span className="font-mono text-xs">{appRes.application_id?.slice(-8)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-500">الحالة</span>
                <span className="font-medium text-brand-700 dark:text-brand-400">{appRes.status}</span>
              </div>
              {plan.holistic_plans_count > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-500">خطة شاملة</span>
                  <span className="font-medium">{plan.holistic_plans_count} طلبات</span>
                </div>
              )}
            </div>

            <button onClick={handleReset} className="btn-primary w-full">
              تسجيل حالة جديدة
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── النموذج ───────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-4">
      <div className="mx-auto max-w-md">
        {/* Header */}
        <div className="mb-6 text-center">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600 mb-3">
            <User className="h-6 w-6 text-white" />
          </div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">
            تسجيل حالة ميدانية
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            سجّل بيانات المستفيد وسيقوم الذكاء الاصطناعي بتحليل الحالة
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* ─── بيانات المستفيد ─── */}
          <div className="card space-y-4">
            <h2 className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <User className="h-4 w-4 text-brand-600" />
              بيانات المستفيد
            </h2>

            <Field label="الاسم الكامل *">
              <input
                type="text"
                required
                value={ben.full_name}
                onChange={(e) => setBen({ ...ben, full_name: e.target.value })}
                placeholder="أحمد محمد العمري"
                className="input-field"
              />
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label="رقم الهوية *">
                <input
                  type="text"
                  required
                  maxLength={10}
                  value={ben.national_id}
                  onChange={(e) => setBen({ ...ben, national_id: e.target.value })}
                  placeholder="1012345678"
                  dir="ltr"
                  className="input-field"
                />
              </Field>
              <Field label="الهاتف *">
                <div className="relative">
                  <Phone className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                  <input
                    type="tel"
                    required
                    value={ben.phone}
                    onChange={(e) => setBen({ ...ben, phone: e.target.value })}
                    placeholder="05xxxxxxxx"
                    dir="ltr"
                    className="input-field pr-8"
                  />
                </div>
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Field label="المدينة">
                <div className="relative">
                  <MapPin className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                  <input
                    type="text"
                    value={ben.city}
                    onChange={(e) => setBen({ ...ben, city: e.target.value })}
                    placeholder="الرياض"
                    className="input-field pr-8"
                  />
                </div>
              </Field>
              <Field label="الحي">
                <input
                  type="text"
                  value={ben.district}
                  onChange={(e) => setBen({ ...ben, district: e.target.value })}
                  placeholder="العزيزية"
                  className="input-field"
                />
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Field label="أفراد الأسرة">
                <div className="relative">
                  <Users className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                  <input
                    type="number"
                    min={1}
                    value={ben.family_size}
                    onChange={(e) => setBen({ ...ben, family_size: +e.target.value })}
                    className="input-field pr-8"
                  />
                </div>
              </Field>
              <Field label="الدخل الشهري (ر.س)">
                <div className="relative">
                  <DollarSign className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                  <input
                    type="number"
                    min={0}
                    value={ben.monthly_income}
                    onChange={(e) => setBen({ ...ben, monthly_income: +e.target.value })}
                    className="input-field pr-8"
                  />
                </div>
              </Field>
            </div>

            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={ben.is_employed}
                  onChange={(e) => setBen({ ...ben, is_employed: e.target.checked })}
                  className="h-4 w-4 rounded accent-brand-600"
                />
                موظف
              </label>
              <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={ben.has_disability}
                  onChange={(e) => setBen({ ...ben, has_disability: e.target.checked })}
                  className="h-4 w-4 rounded accent-brand-600"
                />
                ذوي الإعاقة
              </label>
            </div>
          </div>

          {/* ─── تقرير الحالة الميدانية ─── */}
          <div className="card space-y-4">
            <h2 className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <FileText className="h-4 w-4 text-brand-600" />
              تقرير الحالة الميدانية
              <span className="mr-auto text-xs text-brand-600 dark:text-brand-400">
                يُحلَّل بالذكاء الاصطناعي
              </span>
            </h2>
            <textarea
              rows={3}
              value={ben.field_notes}
              onChange={(e) => setBen({ ...ben, field_notes: e.target.value })}
              placeholder="مثال: يعاني من مرض مزمن ويسكن في إيجار مرتفع، لديه أطفال في سن المدرسة..."
              className="input-field resize-none"
            />
            <p className="text-xs text-slate-400 dark:text-slate-500">
              كلما كان التقرير أدق، كلما أنتج الذكاء الاصطناعي خطة تدخل أشمل
            </p>
          </div>

          {/* ─── بيانات الطلب ─── */}
          <div className="card space-y-4">
            <h2 className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <Zap className="h-4 w-4 text-amber-500" />
              الطلب المرافق
              <span className="mr-auto text-xs text-amber-600 dark:text-amber-400">
                Fast-Track ≤ 5,000 ر.س
              </span>
            </h2>

            <div className="grid grid-cols-2 gap-3">
              <Field label="القطاع">
                <div className="relative">
                  <select
                    value={app.sector}
                    onChange={(e) => setApp({ ...app, sector: e.target.value })}
                    className="input-field appearance-none pr-3"
                  >
                    {SECTORS.map((s) => <option key={s}>{s}</option>)}
                  </select>
                  <ChevronDown className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                </div>
              </Field>
              <Field label="الصندوق">
                <div className="relative">
                  <select
                    value={app.fund_type}
                    onChange={(e) => setApp({ ...app, fund_type: e.target.value })}
                    className="input-field appearance-none pr-3"
                  >
                    {FUND_TYPES.map((f) => <option key={f}>{f}</option>)}
                  </select>
                  <ChevronDown className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                </div>
              </Field>
            </div>

            <Field label="المبلغ المطلوب (ر.س) *">
              <div className="relative">
                <DollarSign className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                <input
                  type="number"
                  required
                  min={1}
                  value={app.requested_amount || ""}
                  onChange={(e) => setApp({ ...app, requested_amount: +e.target.value })}
                  placeholder="1500"
                  className="input-field pr-8"
                />
              </div>
              {app.requested_amount > 0 && app.requested_amount <= 5000 && (
                <p className="mt-1 text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
                  <Zap className="h-3 w-3" /> مؤهل للمسار السريع إذا كانت الأولوية حرجة
                </p>
              )}
            </Field>

            <Field label="وصف الحاجة">
              <input
                type="text"
                value={app.description}
                onChange={(e) => setApp({ ...app, description: e.target.value })}
                placeholder="علاج طارئ / مستلزمات مدرسية…"
                className="input-field"
              />
            </Field>
          </div>

          {/* ─── إرسال ─── */}
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full py-3 text-base"
          >
            {loading ? (
              <><Loader2 className="h-5 w-5 animate-spin" /> جارٍ المعالجة…</>
            ) : (
              <><CheckCircle2 className="h-5 w-5" /> إرسال وتحليل</>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
