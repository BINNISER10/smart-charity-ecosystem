"use client";

import { useState, FormEvent } from "react";
import { HandHeart, Loader2, CheckCircle2 } from "lucide-react";
import toast from "react-hot-toast";
import { donationsApi, DonationCreate, DonationResponse } from "@/lib/api";

const FUND_TYPES = ["الزكاة", "الصدقات", "الأوقاف", "الكفارات"];

const EMPTY: DonationCreate = {
  donor_name: "", donor_phone: "", amount: 0, fund_type: "الزكاة",
};

export default function DonationsPage() {
  const [form, setForm]     = useState<DonationCreate>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState<DonationResponse | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.donor_name || !form.donor_phone || form.amount <= 0) {
      toast.error("الرجاء تعبئة جميع الحقول المطلوبة");
      return;
    }
    setLoading(true);
    try {
      const res = await donationsApi.create(form);
      setResult(res);
      toast.success("تم تسجيل التبرع بنجاح!");
      setForm(EMPTY);
    } catch {
      toast.error("تعذّر تسجيل التبرع");
    } finally {
      setLoading(false);
    }
  };

  const inp = "w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-brand-400 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white";
  const lbl = "block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5";

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <HandHeart className="h-6 w-6 text-brand-600" />
          تسجيل تبرع
        </h1>
        <p className="text-sm text-slate-500 mt-1">أدخل بيانات المتبرع لتسجيل التبرع وإصدار إيصال</p>
      </div>

      {/* Result Card */}
      {result && (
        <div className="rounded-2xl border border-green-200 bg-green-50 p-5 dark:border-green-800 dark:bg-green-900/20 space-y-2">
          <div className="flex items-center gap-2 text-green-700 dark:text-green-400 font-semibold">
            <CheckCircle2 className="h-5 w-5" />
            تم تسجيل التبرع بنجاح
          </div>
          <div className="text-sm text-slate-700 dark:text-slate-300 space-y-1">
            <p>رقم المعاملة: <span className="font-mono text-xs">{result.transaction_id}</span></p>
            <p>المبلغ: <span className="font-bold text-green-700">{result.amount.toLocaleString("ar-SA")} ر.س</span></p>
            <p>الرصيد بعد التبرع: <span className="font-semibold">{result.balance_after.toLocaleString("ar-SA")} ر.س</span></p>
            <p>الصندوق: {result.fund_type}</p>
          </div>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900 space-y-5">
        <div>
          <label className={lbl}>اسم المتبرع <span className="text-red-500">*</span></label>
          <input
            type="text" className={inp} placeholder="محمد أحمد" dir="rtl"
            value={form.donor_name}
            onChange={(e) => setForm({ ...form, donor_name: e.target.value })}
          />
        </div>
        <div>
          <label className={lbl}>رقم الجوال <span className="text-red-500">*</span></label>
          <input
            type="text" className={inp} placeholder="05xxxxxxxx" dir="ltr"
            value={form.donor_phone}
            onChange={(e) => setForm({ ...form, donor_phone: e.target.value })}
          />
        </div>
        <div>
          <label className={lbl}>مبلغ التبرع (ر.س) <span className="text-red-500">*</span></label>
          <input
            type="number" className={inp} placeholder="0" min={1} dir="ltr"
            value={form.amount || ""}
            onChange={(e) => setForm({ ...form, amount: Number(e.target.value) })}
          />
        </div>
        <div>
          <label className={lbl}>نوع الصندوق</label>
          <select
            className={inp}
            value={form.fund_type}
            onChange={(e) => setForm({ ...form, fund_type: e.target.value })}
          >
            {FUND_TYPES.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <HandHeart className="h-4 w-4" />}
          {loading ? "جارٍ التسجيل..." : "تسجيل التبرع"}
        </button>
      </form>
    </div>
  );
}
