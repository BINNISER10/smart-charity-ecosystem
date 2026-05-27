"use client";

import { useState, FormEvent } from "react";
import { Search, Loader2, Phone } from "lucide-react";
import toast from "react-hot-toast";
import { donationsApi, ImpactReportResponse } from "@/lib/api";
import { ImpactCard } from "@/components/impact-card";

export default function ImpactPage() {
  const [phone,   setPhone]   = useState("");
  const [loading, setLoading] = useState(false);
  const [report,  setReport]  = useState<ImpactReportResponse | null>(null);

  const handleSearch = async (e: FormEvent) => {
    e.preventDefault();
    const cleaned = phone.trim();
    if (!cleaned) { toast.error("أدخل رقم الهاتف"); return; }

    setLoading(true);
    setReport(null);
    try {
      const data = await donationsApi.impactReport(cleaned);
      setReport(data);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })
          .response?.data?.detail ?? "لم يتم العثور على بيانات";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          تقرير الأثر
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          أدخل رقم هاتف المتبرع لعرض قصة الأثر الحقيقي لتبرعاته
        </p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="card mb-6">
        <label className="label">رقم هاتف المتبرع</label>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Phone className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="05xxxxxxxx"
              dir="ltr"
              className="input-field pr-9"
            />
          </div>
          <button type="submit" disabled={loading} className="btn-primary px-5">
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            {loading ? "جارٍ البحث…" : "عرض الأثر"}
          </button>
        </div>
      </form>

      {/* Result */}
      {report && (
        <ImpactCard
          phone={report.donor_phone}
          report={report.report}
          generatedAt={report.generated_at}
        />
      )}

      {/* Placeholder */}
      {!report && !loading && (
        <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 py-16 dark:border-slate-700">
          <Phone className="h-10 w-10 text-slate-300 dark:text-slate-600 mb-3" />
          <p className="text-sm text-slate-400 dark:text-slate-500">
            ابحث برقم هاتف لعرض قصة الأثر
          </p>
        </div>
      )}
    </div>
  );
}
