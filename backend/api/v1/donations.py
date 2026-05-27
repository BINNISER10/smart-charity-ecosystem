#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Donations Router — /api/v1/donations
POST /                          — تسجيل تبرع (مع ربط اختياري بطلب)
GET  /impact-report/{phone}     — تقرير الأثر الفوري للمتبرع
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict

_V1      = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.dirname(os.path.dirname(_V1))
_ROOT    = os.path.dirname(_BACKEND)
for _p in (_ROOT, _BACKEND):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_tenant
from core import get_eco, save_eco
from schemas import DonationCreate, DonationResponse, ImpactReportResponse, TenantContext
from smart_charity_ecosystem import FundType

logger = logging.getLogger("api.v1.donations")
router = APIRouter(prefix="/donations", tags=["Donations"])


# ── POST / ────────────────────────────────────────────────────────────────────
@router.post(
    "",
    status_code=201,
    response_model=DonationResponse,
    summary="تسجيل تبرع",
)
async def receive_donation(
    data: DonationCreate,
    tenant: TenantContext = Depends(get_current_tenant),
) -> DonationResponse:
    eco = get_eco(tenant.tenant_id)

    try:
        fund_type = FundType(data.fund_type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"نوع صندوق غير صالح: {data.fund_type}")

    # اختياري: التحقق من وجود الطلب المرتبط
    if data.application_id:
        app = eco._all_applications.get(data.application_id)
        if not app or app.tenant_id != tenant.tenant_id:
            raise HTTPException(
                status_code=404,
                detail=f"الطلب '{data.application_id}' غير موجود لهذا المستأجر",
            )

    ok, msg = eco.finance.receive_donation(
        donor_name=data.donor_name,
        donor_phone=data.donor_phone,
        amount=data.amount,
        fund_type=fund_type,
        executor_id=tenant.username,
        application_id=data.application_id,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    # استخراج آخر معاملة (هي التبرع المسجَّل للتو)
    txns = eco.finance.get_transactions(limit=1)
    if not txns:
        raise HTTPException(status_code=500, detail="لم يُسجَّل التبرع في المعاملات")
    txn = txns[-1]

    save_eco(tenant.tenant_id)

    return DonationResponse(
        transaction_id=txn.transaction_id,
        donor_name=data.donor_name,
        donor_phone=data.donor_phone,
        amount=txn.amount,
        fund_type=txn.fund_type.value,
        balance_after=txn.balance_after,
        application_id=txn.application_id,
        timestamp=txn.timestamp.isoformat(),
        message=msg,
    )


# ── GET /impact-report/{phone} ────────────────────────────────────────────────
@router.get(
    "/impact-report/{donor_phone}",
    response_model=ImpactReportResponse,
    summary="تقرير أثر التبرع للمتبرع",
    description=(
        "يعرض قصة الأثر الحقيقي لتبرعات المتبرع: "
        "كل تبرع مرتبط بطلب تم صرفه يُشعل جملة 'تبرعك ساهم في إنجاز…'"
    ),
)
async def get_impact_report(
    donor_phone: str,
    tenant: TenantContext = Depends(get_current_tenant),
) -> ImpactReportResponse:
    eco = get_eco(tenant.tenant_id)

    report_text = eco.finance.generate_impact_report(
        donor_phone=donor_phone,
        applications=eco._all_applications,
    )

    return ImpactReportResponse(
        donor_phone=donor_phone,
        report=report_text,
        generated_at=datetime.now().isoformat(),
    )
