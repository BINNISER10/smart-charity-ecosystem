"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Heart,
  LogOut,
  ChevronRight,
  Sparkles,
  Users,
  FileText,
  HandHeart,
} from "lucide-react";
import { clsx } from "clsx";
import toast from "react-hot-toast";
import { clearSession, getTenantId } from "@/lib/auth";

const NAV = [
  { href: "/admin",              label: "لوحة التحكم",   icon: LayoutDashboard },
  { href: "/admin/beneficiaries",label: "المستفيدون",    icon: Users },
  { href: "/admin/applications", label: "الطلبات",       icon: FileText },
  { href: "/admin/donations",    label: "التبرعات",      icon: HandHeart },
  { href: "/admin/impact",       label: "تقارير الأثر",  icon: Sparkles },
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
    <aside className="flex h-screen w-64 flex-col bg-gradient-to-b from-brand-900 to-brand-950 shadow-xl">
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/15 backdrop-blur">
          <Heart className="h-5 w-5 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-white leading-tight">منظومة الخير</p>
          <p className="text-xs text-brand-300 mt-0.5">{tenant}</p>
        </div>
      </div>

      {/* تسمية القسم */}
      <p className="px-5 pt-5 pb-2 text-[10px] font-bold uppercase tracking-widest text-brand-400/70">
        القائمة الرئيسية
      </p>

      {/* Nav */}
      <nav className="flex-1 space-y-0.5 px-3">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/admin" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all",
                active
                  ? "bg-white/15 text-white shadow-sm"
                  : "text-brand-200 hover:bg-white/8 hover:text-white"
              )}
            >
              <div className={clsx(
                "flex h-7 w-7 items-center justify-center rounded-lg transition-all",
                active ? "bg-white/20" : "bg-white/5"
              )}>
                <Icon className="h-3.5 w-3.5" />
              </div>
              <span className="flex-1">{label}</span>
              {active && (
                <ChevronRight className="h-3 w-3 text-white/60" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="px-3 pb-5 border-t border-white/10 pt-4">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-red-300 transition hover:bg-red-500/15 hover:text-red-200"
        >
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-500/10">
            <LogOut className="h-3.5 w-3.5" />
          </div>
          تسجيل الخروج
        </button>
      </div>
    </aside>
  );
}
