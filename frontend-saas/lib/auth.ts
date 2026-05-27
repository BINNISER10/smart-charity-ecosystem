/**
 * auth.ts — Token & Session Helpers
 * يخزّن JWT في cookie (مدة 24 ساعة) لدعم الـ middleware
 * ويحفظ role في cookie منفصلة للتوجيه (Role-Based Routing).
 */
import Cookies from "js-cookie";

const TOKEN_KEY = "scs_token";
const ROLE_KEY  = "scs_role";
const TENANT_KEY = "scs_tenant";

const COOKIE_OPTS: Cookies.CookieAttributes = {
  expires: 1,      // يوم واحد
  sameSite: "Lax",
  secure: process.env.NODE_ENV === "production",
};

export function saveSession(token: string, role: string, tenantId: string) {
  Cookies.set(TOKEN_KEY,  token,    COOKIE_OPTS);
  Cookies.set(ROLE_KEY,   role,     COOKIE_OPTS);
  Cookies.set(TENANT_KEY, tenantId, COOKIE_OPTS);
}

export function getToken(): string | undefined {
  return Cookies.get(TOKEN_KEY);
}

export function getRole(): string | undefined {
  return Cookies.get(ROLE_KEY);
}

export function getTenantId(): string | undefined {
  return Cookies.get(TENANT_KEY);
}

export function clearSession() {
  Cookies.remove(TOKEN_KEY);
  Cookies.remove(ROLE_KEY);
  Cookies.remove(TENANT_KEY);
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function redirectAfterLogin(role: string): string {
  if (role === "field_worker") return "/field-worker";
  return "/admin";
}
