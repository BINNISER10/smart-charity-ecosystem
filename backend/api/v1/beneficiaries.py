#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Beneficiaries Router — /api/v1/beneficiaries
GET  /            — قائمة المستفيدين (مع خيار إظهار المؤرشَفين)
POST /            — تسجيل مستفيد جديد + Holistic AI Triage
GET  /{id}        — تفاصيل مستفيد واحد
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, List

# ── sys.path ──────────────────────────────────────────────────────────────────
_V1      = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(os.path.dirname(_V1))
_ROOT    = os.path.dirname(_BACKEND)
for _p in (_ROOT, _BACKEND):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_tenant
from core import get_eco, save_eco
from schemas import BeneficiaryCreate, HolisticPlanResponse, TenantContext
from smart_charity_ecosystem import Address, Beneficiary, HijriCalendar

logger = logging.getLogger("api.v1.beneficiaries")
router = APIRouter(prefix="/beneficiaries", tags=["Beneficiaries"])


# ── مساعد التسلسل ─────────────────────────────────────────────────────────────
def _serialize(b: Beneficiary) -> Dict[str, Any]:
    return {
        "beneficiary_id":   b.beneficiary_id,
        "full_name":        b.full_name,
        "national_id":      b.national_id,
        "phone":            b.phone,
        "city":             b.address.city,
        "district":         b.address.district,
        "family_size":      b.family_size,
        "monthly_income":   b.monthly_income,
        "is_employed":      b.is_employed,
        "has_disability":   b.has_disability,
        "is_eligible":      b.is_eligible,
        "eligibility_notes": b.eligibility_notes,
        "is_archived":      b.is_archived,
        "tenant_id":        b.tenant_id,
        "registration_date":   str(b.registration_date),
        "registration_date_h": HijriCalendar.dual(b.registration_date),
    }


# ── GET / ─────────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[Dict[str, Any]], summary="قائمة المستفيدين")
async def list_beneficiaries(
    include_archived: bool = False,
    tenant: TenantContext = Depends(get_current_tenant),
) -> List[Dict[str, Any]]:
    eco = get_eco(tenant.tenant_id)
    return [
        _serialize(b)
        for b in eco._beneficiaries.values()
        if b.tenant_id == tenant.tenant_id
        and (include_archived or not b.is_archived)
    ]


# ── POST / ────────────────────────────────────────────────────────────────────
@router.post(
    "/",
    status_code=201,
    response_model=HolisticPlanResponse,
    summary="تسجيل مستفيد + Holistic AI Triage",
)
async def create_beneficiary(
    data: BeneficiaryCreate,
    tenant: TenantContext = Depends(get_current_tenant),
) -> HolisticPlanResponse:
    eco = get_eco(tenant.tenant_id)

    # بناء كائن المستفيد
    ben = Beneficiary(
        full_name=data.full_name,
        national_id=data.national_id,
        phone=data.phone,
        address=Address(city=data.city, district=data.district),
        family_size=data.family_size,
        monthly_income=data.monthly_income,
        is_employed=data.is_employed,
        has_disability=data.has_disability,
        tenant_id=tenant.tenant_id,
    )

    # تسجيل + تقييم الأهلية
    is_eligible, reason = eco.register_beneficiary(ben)

    # Holistic AI Triage — ينشئ خطة طلبات متعددة من الملاحظات الميدانية
    plans: List[Dict[str, Any]] = []
    if data.field_notes:
        generated = eco.ai.generate_holistic_plan(data.field_notes, ben)
        plans = [
            {
                "application_id": p.application_id,
                "sector":          p.sector.value,
                "requested_amount": p.requested_amount,
                "description":     p.description,
                "priority":        p.priority.value,
            }
            for p in generated
        ]
        logger.info(
            "Holistic plan: %d طلبات للمستفيد %s (tenant=%s)",
            len(plans), ben.beneficiary_id, tenant.tenant_id,
        )

    save_eco(tenant.tenant_id)

    return HolisticPlanResponse(
        beneficiary_id=ben.beneficiary_id,
        is_eligible=bool(is_eligible),
        eligibility_reason=reason,
        holistic_plans_count=len(plans),
        plans=plans,
    )


# ── GET /{id} ─────────────────────────────────────────────────────────────────
@router.get("/{beneficiary_id}", summary="تفاصيل مستفيد")
async def get_beneficiary(
    beneficiary_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
) -> Dict[str, Any]:
    eco = get_eco(tenant.tenant_id)
    b = eco._beneficiaries.get(beneficiary_id)
    if not b or b.tenant_id != tenant.tenant_id:
        raise HTTPException(status_code=404, detail="المستفيد غير موجود")
    return _serialize(b)
