#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Dependencies — deps.py
يُعرِّف دالة get_current_tenant كـ Dependency مُحقَن في جميع المسارات المحمية.
تقرأ JWT من ترويسة Authorization وتستخرج tenant_id + role.
"""
from __future__ import annotations

import logging
import os
import sys

# ── مسار backend/ في sys.path لاستيراد schemas ──────────────────────────────
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas import TenantContext

logger = logging.getLogger("api.deps")

# ── إعدادات JWT ───────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "saas-change-me-in-production-!!1234567890")
ALGORITHM  = "HS256"

# ── محاولة تحميل python-jose ─────────────────────────────────────────────────
try:
    from jose import JWTError, jwt as _jwt  # type: ignore
    _JOSE_OK = True
except ImportError:
    _JOSE_OK = False
    logger.warning(
        "python-jose غير مثبت — تحقق JWT معطّل. "
        "قم بتثبيته: pip install python-jose[cryptography]"
    )

_bearer = HTTPBearer(auto_error=True)


async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> TenantContext:
    """
    FastAPI Dependency — يستخرج TenantContext من JWT.

    يُرمى HTTPException 401 عند:
    - غياب التوكن أو عدم صلاحيته
    - عدم وجود tenant_id في الـ payload
    - عدم تثبيت python-jose (بيئة التطوير فقط)
    """
    if not _JOSE_OK:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="python-jose غير مثبت على الخادم — pip install python-jose[cryptography]",
        )

    token = credentials.credentials
    try:
        payload = _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        logger.warning("JWT decode failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توكن غير صالح أو منتهي الصلاحية",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant_id: str = payload.get("tenant_id", "")
    role: str      = payload.get("role", "viewer")
    username: str  = payload.get("sub", "unknown")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="التوكن لا يحتوي على tenant_id — استخدم /api/v1/auth/login أولاً",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TenantContext(tenant_id=tenant_id, role=role, username=username)
