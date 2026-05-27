/**
 * Next.js Middleware — التحقق من الجلسة وتوجيه المستخدم بناءً على الدور.
 * يعمل على Edge Runtime قبل تحميل أي صفحة.
 */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS  = ["/login"];
const FIELD_PATHS   = ["/field-worker"];
const ADMIN_PATHS   = ["/admin"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // مسارات عامة — لا تحتاج توكن
  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const token = request.cookies.get("scs_token")?.value;
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // توجيه بناءً على الدور
  const role = request.cookies.get("scs_role")?.value ?? "";

  if (ADMIN_PATHS.some((p) => pathname.startsWith(p)) && role === "field_worker") {
    return NextResponse.redirect(new URL("/field-worker", request.url));
  }
  if (FIELD_PATHS.some((p) => pathname.startsWith(p)) && role === "admin") {
    return NextResponse.redirect(new URL("/admin", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|fonts|icons).*)",
  ],
};
