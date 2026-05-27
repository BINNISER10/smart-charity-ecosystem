"use client";

import { useQuery } from "@tanstack/react-query";
import { Users, FileText, CheckCircle, Loader2, TrendingUp } from "lucide-react";
import { applicationsApi, beneficiariesApi } from "@/lib/api";

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${color}`}>
        <Icon className="h-6 w-6 text-white" />
      </div>
      <div>
        <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">{value}</p>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const { data: beneficiaries = [], isLoading: loadingBen } = useQuery({
    queryKey: ["beneficiaries"],
    queryFn: () => beneficiariesApi.list(),
  });

  const { data: applications = [], isLoading: loadingApps } = useQuery({
    queryKey: ["applications"],
    queryFn: () => applicationsApi.list(),
  });

  const loading = loadingBen || loadingApps;

  const disbursed = (applications as { status: string }[]).filter(
    (a) => a.status === "تم الصرف"
  ).length;

  const fastTracked = (applications as { fast_tracked?: boolean }[]).filter(
    (a) => a.fast_tracked
  ).length;

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-600" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
          لوحة التحكم
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          نظرة عامة على نشاط المستأجر
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatCard
          label="المستفيدون"
          value={beneficiaries.length}
          icon={Users}
          color="bg-blue-500"
        />
        <StatCard
          label="إجمالي الطلبات"
          value={applications.length}
          icon={FileText}
          color="bg-brand-600"
        />
        <StatCard
          label="طلبات مصروفة"
          value={disbursed}
          icon={CheckCircle}
          color="bg-emerald-500"
        />
        <StatCard
          label="مسار سريع ⚡"
          value={fastTracked}
          icon={TrendingUp}
          color="bg-amber-500"
        />
      </div>

      {/* Recent Applications */}
      <div className="card">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-4">
          آخر الطلبات
        </h2>
        {(applications as Record<string, string>[]).length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-8">لا توجد طلبات بعد</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-700 text-right">
                  <th className="pb-3 font-medium text-slate-500 dark:text-slate-400">
                    معرّف الطلب
                  </th>
                  <th className="pb-3 font-medium text-slate-500 dark:text-slate-400">القطاع</th>
                  <th className="pb-3 font-medium text-slate-500 dark:text-slate-400">المبلغ</th>
                  <th className="pb-3 font-medium text-slate-500 dark:text-slate-400">الأولوية</th>
                  <th className="pb-3 font-medium text-slate-500 dark:text-slate-400">الحالة</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50 dark:divide-slate-800">
                {(applications as Record<string, string>[]).slice(-10).reverse().map((a) => (
                  <tr key={a.application_id}>
                    <td className="py-3 font-mono text-xs text-slate-600 dark:text-slate-400">
                      {a.application_id?.slice(-8)}
                    </td>
                    <td className="py-3 text-slate-800 dark:text-slate-200">{a.sector}</td>
                    <td className="py-3 text-slate-800 dark:text-slate-200">
                      {Number(a.requested_amount).toLocaleString("ar-SA")} ر.س
                    </td>
                    <td className="py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                          a.priority === "حرجة"
                            ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                            : a.priority === "عالية"
                            ? "bg-orange-100 text-orange-700"
                            : "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                        }`}
                      >
                        {a.priority}
                      </span>
                    </td>
                    <td className="py-3">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                          a.status === "تم الصرف"
                            ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                            : a.status === "معتمد"
                            ? "bg-blue-100 text-blue-700"
                            : "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300"
                        }`}
                      >
                        {a.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
