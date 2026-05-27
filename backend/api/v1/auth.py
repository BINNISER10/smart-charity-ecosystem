#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auth Router — /api/v1/auth
تسجيل الدخول وإصدار JWT يحمل tenant_id + role.
المستخدمون مُخزَّنون حالياً في قاموس وهمي (Mock) — يُستبدل بـ Supabase Auth لاحقاً.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

# ── مسارات sys.path ───────────────────────────────────────────────────────────
_V1_DIR     = os.path.dirname(os.path.abspath(__file__))
_BACKEND    = os.path.dirname(os.path.dirname(_V1_DIR))
_ROOT       = os.path.dirname(_BACKEND)
for _p in (_ROOT, _BACKEND):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from fastapi import APIRouter, HTTPException

from schemas import LoginRequest, TokenResponse

logger = logging.getLogger("api.v1.auth")

# ── إعدادات JWT ───────────────────────────────────────────────────────────────
SECRET_KEY          = os.getenv("JWT_SECRET_KEY", "saas-change-me-in-production-!!1234567890")
ALGORITHM           = "HS256"
TOKEN_EXPIRE_HOURS  = int(os.getenv("TOKEN_EXPIRE_HOURS", "24"))

try:
    from jose import jwt as _jwt  # type: ignore
    _JOSE_OK = True
except ImportError:
    _JOSE_OK = False

# ── مستخدمو النظام (Mock — يُستبدَل بقاعدة بيانات) ─────────────────────────
_MOCK_USERS: dict[str, dict] = {
    # org_a — المنظمة الأولى
    "admin@org_a":   {"password": "admin123", "tenant_id": "org_a", "role": "admin"},
    "manager@org_a": {"password": "mgr456",   "tenant_id": "org_a", "role": "manager"},
    "field@org_a":   {"password": "field789", "tenant_id": "org_a", "role": "field_worker"},
    # org_b — المنظمة الثانية
    "admin@org_b":   {"password": "admin123", "tenant_id": "org_b", "role": "admin"},
    "field@org_b":   {"password": "field789", "tenant_id": "org_b", "role": "field_worker"},
}

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    return _jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="تسجيل الدخول",
    description="يُرجع JWT يحتوي على tenant_id و role لاستخدامه في كل الطلبات التالية.",
)
async def login(req: LoginRequest) -> TokenResponse:
    if not _JOSE_OK:
        raise HTTPException(
            status_code=500,
            detail="python-jose غير مثبت — pip install python-jose[cryptography]",
        )

    user = _MOCK_USERS.get(req.username)
    if not user or user["password"] != req.password:
        logger.warning("محاولة دخول فاشلة: %s", req.username)
        raise HTTPException(
            status_code=401,
            detail="اسم المستخدم أو كلمة المرور غير صحيحة",
        )
    if user["tenant_id"] != req.tenant_id:
        raise HTTPException(
            status_code=403,
            detail=f"الحساب '{req.username}' لا ينتمي للمستأجر '{req.tenant_id}'",
        )

    token = _create_access_token(
        {
            "sub":       req.username,
            "tenant_id": user["tenant_id"],
            "role":      user["role"],
        },
        timedelta(hours=TOKEN_EXPIRE_HOURS),
    )
    logger.info("تسجيل دخول ناجح: %s / tenant=%s", req.username, user["tenant_id"])
    return TokenResponse(
        access_token=token,
        tenant_id=user["tenant_id"],
        role=user["role"],
    )
