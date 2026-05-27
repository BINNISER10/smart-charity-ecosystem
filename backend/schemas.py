#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic Schemas — SaaS API v1
تُعرِّف جميع النماذج الداخلة والخارجة من طبقة الـ API.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════════
#  Auth
# ═══════════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str = Field(..., examples=["admin@org_a"])
    password: str = Field(..., examples=["admin123"])
    tenant_id: str = Field(..., examples=["org_a"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    role: str


class TenantContext(BaseModel):
    """سياق المستأجر المستخرج من الـ JWT — يُحقن في جميع المسارات."""
    tenant_id: str
    role: str
    username: str


# ═══════════════════════════════════════════════════════════════════════════════
#  Beneficiaries
# ═══════════════════════════════════════════════════════════════════════════════

class BeneficiaryCreate(BaseModel):
    full_name: str = Field(..., min_length=2, examples=["أحمد محمد العمري"])
    national_id: str = Field(..., min_length=10, max_length=10, examples=["1012345678"])
    phone: str = Field(..., examples=["0512345678"])
    city: str = Field(..., examples=["الرياض"])
    district: str = Field(..., examples=["العزيزية"])
    family_size: int = Field(..., ge=1, le=30)
    monthly_income: float = Field(..., ge=0.0)
    is_employed: bool = False
    has_disability: bool = False
    field_notes: Optional[str] = Field(
        default=None,
        description="ملاحظات ميدانية لتوليد خطة تدخل شاملة (Holistic Plan)",
        examples=["يعاني من مرض مزمن ويسكن في إيجار مرتفع ويحتاج غذاءً"],
    )


class BeneficiaryResponse(BaseModel):
    beneficiary_id: str
    full_name: str
    national_id: str
    phone: str
    city: str
    district: str
    family_size: int
    monthly_income: float
    is_employed: bool
    has_disability: bool
    is_eligible: Optional[bool]
    eligibility_notes: str
    is_archived: bool
    tenant_id: str
    registration_date: str
    registration_date_h: Optional[str] = None


class HolisticPlanResponse(BaseModel):
    beneficiary_id: str
    is_eligible: bool
    eligibility_reason: str
    holistic_plans_count: int
    plans: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════════════════
#  Applications
# ═══════════════════════════════════════════════════════════════════════════════

class ApplicationCreate(BaseModel):
    beneficiary_id: str
    sector: str = Field(..., examples=["الصحة"])
    requested_amount: float = Field(..., gt=0)
    fund_type: str = Field(..., examples=["الزكاة"])
    description: str = Field(..., min_length=5)
    supporting_docs: List[str] = []


class ApplicationResponse(BaseModel):
    application_id: str
    beneficiary_id: str
    sector: str
    fund_type: str
    requested_amount: float
    approved_amount: float
    status: str
    priority: str
    ai_score: float
    ai_recommendation: str
    submission_date: str
    tenant_id: str
    fast_tracked: bool = False
    message: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
#  Donations
# ═══════════════════════════════════════════════════════════════════════════════

class DonationCreate(BaseModel):
    donor_name: str = Field(..., min_length=2)
    donor_phone: str
    amount: float = Field(..., gt=0)
    fund_type: str = Field(..., examples=["الزكاة"])
    application_id: Optional[str] = Field(
        default=None,
        description="ربط اختياري بطلب مستفيد محدد (Impact Loop)",
    )


class DonationResponse(BaseModel):
    transaction_id: str
    donor_name: str
    donor_phone: str
    amount: float
    fund_type: str
    balance_after: float
    application_id: Optional[str]
    timestamp: str
    message: str


class ImpactReportResponse(BaseModel):
    donor_phone: str
    report: str
    generated_at: str
