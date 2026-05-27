"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Heart,
  LogOut,
  ChevronRight,
  Sparkles,
} from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";
import { clearSession, getTenantId } from "@/lib/auth";

const NAV = [
  { href: "/admin",         label: "لوحة التحكم",   icon: LayoutDashboard },
  { href: "/admin/impact",  label: "تقارير الأثر",  icon: Sparkles },
];

export function Sidebar() {
  const pathname = usePathname();
  const router   = useRouter();
  const tenant   = getTenantId() ?? "—";

  const handleLogout = () => {
    clearSession();
    toast.success("تم تسجيل الخروج");
    router.push("/login");
  };

  return (
    <aside className="flex h-screen w-64 flex-col border-l border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 py-6 border-b border-slate-200 dark:border-slate-700">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600">
          <Heart className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-slate-900 dark:text-white">العمل الخيري</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{tenant}</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                active
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-400"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
              {active && (
                <ChevronRight className="mr-auto h-3.5 w-3.5 text-brand-600 dark:text-brand-400" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="px-3 pb-5">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-red-600 transition hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
        >
          <LogOut className="h-4 w-4" />
          تسجيل الخروج
        </button>
      </div>
    </aside>
  );
}
