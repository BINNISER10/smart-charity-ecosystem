#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applications Router — /api/v1/applications
POST /submit      — تقديم طلب (مع Fast-Track التلقائي للحالات الحرجة)
GET  /            — قائمة الطلبات للمستأجر الحالي
GET  /{id}        — تفاصيل طلب واحد
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, List

_V1      = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(os.path.dirname(_V1))
_ROOT    = os.path.dirname(_BACKEND)
for _p in (_ROOT, _BACKEND):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_tenant
from core import get_eco, save_eco
from schemas import ApplicationCreate, ApplicationResponse, TenantContext
from smart_charity_ecosystem import (
    Application, ApplicationStatus, FundType, HijriCalendar, SectorType,
)

logger = logging.getLogger("api.v1.applications")
router = APIRouter(prefix="/applications", tags=["Applications"])


def _serialize(a: Application) -> Dict[str, Any]:
    return {
        "application_id":   a.application_id,
        "beneficiary_id":   a.beneficiary_id,
        "sector":           a.sector.value,
        "fund_type":        a.fund_type.value,
        "requested_amount": a.requested_amount,
        "approved_amount":  a.approved_amount,
        "status":           a.status.value,
        "priority":         a.priority.value,
        "ai_score":         round(a.ai_score, 2),
        "ai_recommendation": a.ai_recommendation,
        "description":      a.description,
        "submission_date":  str(a.submission_date),
        "submission_date_h": HijriCalendar.dual(a.submission_date),
        "tenant_id":        a.tenant_id,
        "audit_trail":      a.audit_trail[-5:],
    }


# ── POST /submit ──────────────────────────────────────────────────────────────
@router.post(
    "/submit",
    status_code=201,
    summary="تقديم طلب (Fast-Track تلقائي للحالات الحرجة)",
)
async def submit_application(
    data: ApplicationCreate,
    tenant: TenantContext = Depends(get_current_tenant),
) -> Dict[str, Any]:
    eco = get_eco(tenant.tenant_id)

    # التحقق من وجود المستفيد وانتمائه للمستأجر
    ben = eco._beneficiaries.get(data.beneficiary_id)
    if not ben or ben.tenant_id != tenant.tenant_id:
        raise HTTPException(status_code=404, detail="المستفيد غير موجود أو لا ينتمي لهذا المستأجر")

    # تحويل قيم Enum
    try:
        sector    = SectorType(data.sector)
        fund_type = FundType(data.fund_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"قيمة غير صالحة: {exc}")

    # بناء كائن الطلب
    app = Application(
        beneficiary_id=data.beneficiary_id,
        sector=sector,
        fund_type=fund_type,
        requested_amount=data.requested_amount,
        description=data.description,
        supporting_docs=list(data.supporting_docs),
        tenant_id=tenant.tenant_id,
    )

    # تقديم الطلب (الذكاء الاصطناعي + Fast-Track إذا اقتضى الأمر)
    ok, msg = eco.submit_application(app)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    fast_tracked = (app.status == ApplicationStatus.DISBURSED)
    if fast_tracked:
        logger.info(
            "Fast-Track: طلب %s تم صرفه تلقائياً (tenant=%s)",
            app.application_id, tenant.tenant_id,
        )

    save_eco(tenant.tenant_id)

    return {
        **_serialize(app),
        "fast_tracked": fast_tracked,
        "message": msg,
    }


# ── GET / ─────────────────────────────────────────────────────────────────────
@router.get("", response_model=List[Dict[str, Any]], summary="قائمة الطلبات")
async def list_applications(
    status_filter: str = "",
    tenant: TenantContext = Depends(get_current_tenant),
) -> List[Dict[str, Any]]:
    eco = get_eco(tenant.tenant_id)
    apps = [
        a for a in eco._all_applications.values()
        if a.tenant_id == tenant.tenant_id
    ]
    if status_filter:
        apps = [a for a in apps if a.status.value == status_filter]
    return [_serialize(a) for a in apps]


# ── GET /{id} ─────────────────────────────────────────────────────────────────
@router.get("/{application_id}", summary="تفاصيل طلب")
async def get_application(
    application_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
) -> Dict[str, Any]:
    eco = get_eco(tenant.tenant_id)
    a = eco._all_applications.get(application_id)
    if not a or a.tenant_id != tenant.tenant_id:
        raise HTTPException(status_code=404, detail="الطلب غير موجود")
    return _serialize(a)
