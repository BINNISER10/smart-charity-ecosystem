"use client";

import { useEffect, useState } from "react";
import { FileText, Filter, Loader2, Zap } from "lucide-react";
import toast from "react-hot-toast";
import { applicationsApi, ApplicationResponse } from "@/lib/api";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  PENDING:   { label: "قيد الانتظار", color: "bg-yellow-100 text-yellow-700" },
  APPROVED:  { label: "موافق عليه",  color: "bg-green-100 text-green-700" },
  REJECTED:  { label: "مرفوض",       color: "bg-red-100 text-red-600" },
  DISBURSED: { label: "صُرف",         color: "bg-blue-100 text-blue-700" },
  CANCELLED: { label: "ملغى",         color: "bg-slate-100 text-slate-500" },
};

const PRIORITY_COLORS: Record<string, string> = {
  CRITICAL: "bg-red-600 text-white",
  HIGH:     "bg-orange-500 text-white",
  MEDIUM:   "bg-yellow-400 text-slate-900",
  LOW:      "bg-slate-200 text-slate-600",
};

export default function ApplicationsPage() {
  const [list, setList]       = useState<ApplicationResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter]   = useState("");

  const load = (f = filter) => {
    setLoading(true);
    applicationsApi.list(f || undefined)
      .then(setList)
      .catch(() => toast.error("تعذّر تحميل الطلبات"))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <FileText className="h-6 w-6 text-brand-600" />
            الطلبات
          </h1>
          <p className="text-sm text-slate-500 mt-1">إجمالي: {list.length} طلب</p>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <select
            value={filter}
            onChange={(e) => { setFilter(e.target.value); load(e.target.value); }}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm focus:border-brand-400 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          >
            <option value="">كل الطلبات</option>
            {Object.entries(STATUS_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-brand-600" />
        </div>
      ) : list.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-200 py-16 text-center text-slate-400 dark:border-slate-700">
          لا توجد طلبات بعد
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          <table className="w-full text-sm text-right">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr>
                {["رقم الطلب", "القطاع", "المبلغ المطلوب", "المبلغ الموافق", "الأولوية", "درجة AI", "الحالة", "تاريخ التقديم"].map((h) => (
                  <th key={h} className="px-4 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {list.map((a) => {
                const st = STATUS_LABELS[a.status] ?? { label: a.status, color: "bg-slate-100 text-slate-600" };
                const pc = PRIORITY_COLORS[a.priority] ?? "bg-slate-100 text-slate-600";
                return (
                  <tr key={a.application_id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">{a.application_id.slice(-8)}</td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{a.sector}</td>
                    <td className="px-4 py-3">{a.requested_amount.toLocaleString("ar-SA")} ر.س</td>
                    <td className="px-4 py-3 font-semibold text-green-700">{a.approved_amount.toLocaleString("ar-SA")} ر.س</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${pc}`}>
                        {a.priority === "CRITICAL" && <Zap className="h-3 w-3" />}
                        {a.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 rounded-full bg-slate-100 dark:bg-slate-700">
                          <div
                            className="h-1.5 rounded-full bg-brand-600"
                            style={{ width: `${Math.min(a.ai_score, 100)}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-500">{a.ai_score.toFixed(0)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${st.color}`}>{st.label}</span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">{a.submission_date_h}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
