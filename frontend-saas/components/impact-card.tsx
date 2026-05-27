"use client";

import { Sparkles, Heart, CheckCircle2, Clock } from "lucide-react";

interface ImpactCardProps {
  phone: string;
  report: string;
  generatedAt: string;
}

export function ImpactCard({ phone, report, generatedAt }: ImpactCardProps) {
  const lines = report.split("\n").filter(Boolean);
  const summary = lines[0] ?? "";
  const details = lines.slice(1);

  const hasDisbursed = details.some((l) => l.startsWith("✅"));
  const hasPending   = details.some((l) => l.startsWith("⏳"));

  return (
    <div className="relative overflow-hidden rounded-2xl border border-brand-200 bg-gradient-to-br from-brand-50 to-white p-6 shadow-md dark:border-brand-800 dark:from-brand-950 dark:to-slate-900">
      {/* Background decoration */}
      <div className="pointer-events-none absolute -left-8 -top-8 h-40 w-40 rounded-full bg-brand-100/50 dark:bg-brand-900/20" />
      <div className="pointer-events-none absolute -bottom-4 -right-4 h-24 w-24 rounded-full bg-brand-100/30 dark:bg-brand-900/10" />

      {/* Header */}
      <div className="relative mb-5 flex items-center gap-3">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-600 shadow-lg shadow-brand-200 dark:shadow-brand-900">
          <Heart className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400">تقرير الأثر للمتبرع</p>
          <p className="font-semibold text-slate-800 dark:text-white" dir="ltr">
            {phone}
          </p>
        </div>
        <div className="mr-auto">
          <Sparkles className="h-5 w-5 text-brand-500" />
        </div>
      </div>

      {/* Summary row */}
      <div className="relative mb-4 rounded-xl bg-white/70 p-3 shadow-sm dark:bg-slate-800/60">
        <p className="text-sm font-semibold text-brand-700 dark:text-brand-400">{summary}</p>
      </div>

      {/* Detail lines */}
      {details.length > 0 && (
        <ul className="relative space-y-2">
          {details.map((line, i) => {
            const isDisbursed = line.startsWith("✅");
            const isPending   = line.startsWith("⏳");
            return (
              <li
                key={i}
                className={`flex items-start gap-2.5 rounded-lg p-3 text-sm ${
                  isDisbursed
                    ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-400"
                    : isPending
                    ? "bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-400"
                    : "bg-slate-50 text-slate-700 dark:bg-slate-800/50 dark:text-slate-300"
                }`}
              >
                {isDisbursed ? (
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                ) : isPending ? (
                  <Clock className="mt-0.5 h-4 w-4 shrink-0" />
                ) : (
                  <span className="mt-0.5 h-4 w-4 shrink-0 text-center text-xs">•</span>
                )}
                <span>{line.replace(/^[✅⏳•]\s*/, "")}</span>
              </li>
            );
          })}
        </ul>
      )}

      {/* Status badge */}
      <div className="relative mt-4 flex items-center justify-between text-xs text-slate-400 dark:text-slate-500">
        <span>تم الإنشاء: {new Date(generatedAt).toLocaleString("ar-SA")}</span>
        {hasDisbursed && (
          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
            أثر محقَّق ✓
          </span>
        )}
        {!hasDisbursed && hasPending && (
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
            قيد التنفيذ
          </span>
        )}
      </div>
    </div>
  );
}
