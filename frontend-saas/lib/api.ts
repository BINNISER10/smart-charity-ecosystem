/**
 * api.ts — Centralized API Client
 * كل استدعاءات الـ backend تمر من هنا.
 * الـ base URL يُعيَّد تلقائياً عبر next.config.mjs → /api/v1/*
 */

import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import { getToken } from "@/lib/auth";

// ── أنواع البيانات ────────────────────────────────────────────────────────────

export interface LoginPayload {
  username: string;
  password: string;
  tenant_id: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  tenant_id: string;
  role: string;
}

export interface BeneficiaryCreate {
  full_name: string;
  national_id: string;
  phone: string;
  city: string;
  district: string;
  family_size: number;
  monthly_income: number;
  is_employed: boolean;
  has_disability: boolean;
  field_notes?: string;
}

export interface HolisticPlanResponse {
  beneficiary_id: string;
  is_eligible: boolean;
  eligibility_reason: string;
  holistic_plans_count: number;
  plans: Array<{
    application_id: string;
    sector: string;
    requested_amount: number;
    description: string;
    priority: string;
  }>;
}

export interface ApplicationCreate {
  beneficiary_id: string;
  sector: string;
  requested_amount: number;
  fund_type: string;
  description: string;
  supporting_docs?: string[];
}

export interface ApplicationResponse {
  application_id: string;
  beneficiary_id: string;
  sector: string;
  fund_type: string;
  requested_amount: number;
  approved_amount: number;
  status: string;
  priority: string;
  ai_score: number;
  ai_recommendation: string;
  description: string;
  submission_date: string;
  submission_date_h: string;
  tenant_id: string;
  fast_tracked: boolean;
  message: string;
}

export interface DonationCreate {
  donor_name: string;
  donor_phone: string;
  amount: number;
  fund_type: string;
  application_id?: string;
}

export interface DonationResponse {
  transaction_id: string;
  donor_name: string;
  donor_phone: string;
  amount: number;
  fund_type: string;
  balance_after: number;
  application_id: string | null;
  timestamp: string;
  message: string;
}

export interface ImpactReportResponse {
  donor_phone: string;
  report: string;
  generated_at: string;
}

// ── إنشاء مثيل axios ─────────────────────────────────────────────────────────

function createClient(): AxiosInstance {
  const client = axios.create({ baseURL: "/api/v1" });

  client.interceptors.request.use((config) => {
    const token = getToken();
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (res) => res,
    (err) => {
      if (err.response?.status === 401) {
        // إعادة التوجيه لصفحة الدخول عند انتهاء التوكن
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
      return Promise.reject(err);
    }
  );

  return client;
}

export const apiClient = createClient();

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (payload: LoginPayload) =>
    apiClient.post<TokenResponse>("/auth/login", payload).then((r) => r.data),
};

// ── Beneficiaries ─────────────────────────────────────────────────────────────

export const beneficiariesApi = {
  list: (includeArchived = false) =>
    apiClient
      .get<Record<string, unknown>[]>("/beneficiaries", {
        params: { include_archived: includeArchived },
      })
      .then((r) => r.data),

  create: (data: BeneficiaryCreate) =>
    apiClient
      .post<HolisticPlanResponse>("/beneficiaries", data)
      .then((r) => r.data),

  get: (id: string) =>
    apiClient.get<Record<string, unknown>>(`/beneficiaries/${id}`).then((r) => r.data),
};

// ── Applications ──────────────────────────────────────────────────────────────

export const applicationsApi = {
  submit: (data: ApplicationCreate) =>
    apiClient
      .post<ApplicationResponse>("/applications/submit", data)
      .then((r) => r.data),

  list: (statusFilter?: string) =>
    apiClient
      .get<ApplicationResponse[]>("/applications", {
        params: statusFilter ? { status_filter: statusFilter } : {},
      })
      .then((r) => r.data),

  get: (id: string) =>
    apiClient.get<ApplicationResponse>(`/applications/${id}`).then((r) => r.data),

  approve: (id: string, approved_amount: number, notes = "") =>
    apiClient
      .post<ApplicationResponse>(`/applications/${id}/approve`, { approved_amount, notes })
      .then((r) => r.data),

  reject: (id: string, reason = "مرفوض من قِبَل المدير") =>
    apiClient
      .post<ApplicationResponse>(`/applications/${id}/reject`, { reason })
      .then((r) => r.data),

  disburse: (id: string) =>
    apiClient
      .post<ApplicationResponse>(`/applications/${id}/disburse`, {})
      .then((r) => r.data),
};

// ── Donations ─────────────────────────────────────────────────────────────────

export const donationsApi = {
  create: (data: DonationCreate) =>
    apiClient.post<DonationResponse>("/donations", data).then((r) => r.data),

  impactReport: (phone: string) =>
    apiClient
      .get<ImpactReportResponse>(`/donations/impact-report/${encodeURIComponent(phone)}`)
      .then((r) => r.data),
};
