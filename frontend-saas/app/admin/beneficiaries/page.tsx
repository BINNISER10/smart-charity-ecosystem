"use client";

import { useEffect, useState } from "react";
import { Users, Search, UserCheck, UserX, Loader2, Plus } from "lucide-react";
import toast from "react-hot-toast";
import { beneficiariesApi } from "@/lib/api";
import Link from "next/link";

export default function BeneficiariesPage() {
  const [list, setList]       = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery]     = useState("");

  useEffect(() => {
    beneficiariesApi.list(true)
      .then(setList)
      .catch(() => toast.error("تعذّر تحميل المستفيدين"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = list.filter((b) =>
    String(b.full_name ?? "").includes(query) ||
    String(b.national_id ?? "").includes(query) ||
    String(b.city ?? "").includes(query)
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Users className="h-6 w-6 text-brand-600" />
            المستفيدون
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            إجمالي المستفيدين المسجَّلين: <span className="font-semibold">{list.length}</span>
          </p>
        </div>
        <Link
          href="/field-worker"
          className="flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 transition"
        >
          <Plus className="h-4 w-4" />
          تسجيل مستفيد
        </Link>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute right-3 top-2.5 h-4 w-4 text-slate-400" />
        <input
          type="text"
          placeholder="ابحث بالاسم أو الهوية أو المدينة..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-xl border border-slate-200 bg-white py-2 pr-9 pl-4 text-sm focus:border-brand-400 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
          dir="rtl"
        />
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-brand-600" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-200 py-16 text-center text-slate-400 dark:border-slate-700">
          {query ? "لا نتائج للبحث" : "لا يوجد مستفيدون مسجَّلون بعد"}
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          <table className="w-full text-sm text-right">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr>
                {["الاسم", "الهوية", "المدينة", "أفراد الأسرة", "الدخل الشهري", "مؤهَّل", "الحالة"].map((h) => (
                  <th key={h} className="px-4 py-3 text-xs font-semibold text-slate-500 dark:text-slate-400">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {filtered.map((b) => (
                <tr key={String(b.beneficiary_id)} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition">
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">{String(b.full_name ?? "—")}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">{String(b.national_id ?? "—")}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{String(b.city ?? "—")}</td>
                  <td className="px-4 py-3 text-center">{String(b.family_size ?? "—")}</td>
                  <td className="px-4 py-3">{Number(b.monthly_income ?? 0).toLocaleString("ar-SA")} ر.س</td>
                  <td className="px-4 py-3">
                    {b.is_eligible ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700">
                        <UserCheck className="h-3 w-3" /> مؤهَّل
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-1 text-xs font-medium text-red-600">
                        <UserX className="h-3 w-3" /> غير مؤهَّل
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {b.is_archived ? (
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-500">مؤرشَف</span>
                    ) : (
                      <span className="rounded-full bg-blue-100 px-2.5 py-1 text-xs text-blue-700">نشط</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
