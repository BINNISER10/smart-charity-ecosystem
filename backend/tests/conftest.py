"""
conftest.py — إعداد بيئة الاختبار لـ API Integration Tests
يضبط sys.path ليجد:
  - smart_charity_ecosystem.py (جذر المشروع)
  - main.py, core.py, etc.   (backend/)
"""
from __future__ import annotations

import os
import sys

# ── إعداد المسارات (يجب قبل أي import من المشروع) ──────────────────────────
_TESTS_DIR   = os.path.dirname(os.path.abspath(__file__))   # backend/tests/
_BACKEND_DIR = os.path.dirname(_TESTS_DIR)                  # backend/
_PROJECT_ROOT = os.path.dirname(_BACKEND_DIR)               # project root/

for _p in (_PROJECT_ROOT, _BACKEND_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── JWT Helper ───────────────────────────────────────────────────────────────
from datetime import datetime, timedelta, timezone

try:
    from jose import jwt as _jose_jwt
    _JOSE_AVAILABLE = True
except ImportError:
    _JOSE_AVAILABLE = False

import pytest

SECRET_KEY   = os.getenv("JWT_SECRET_KEY", "ci-test-secret-do-not-use-in-production")
TEST_TENANT  = "ci_test_tenant"
OTHER_TENANT = "ci_other_tenant"


def _make_token(tenant_id: str, role: str = "admin") -> str:
    """ينشئ JWT صالح للاختبار."""
    if not _JOSE_AVAILABLE:
        raise RuntimeError("python-jose غير مثبت — pip install python-jose[cryptography]")
    payload = {
        "sub":       f"ci@{tenant_id}",
        "tenant_id": tenant_id,
        "role":      role,
        "exp":       datetime.now(timezone.utc) + timedelta(hours=2),
    }
    return _jose_jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@pytest.fixture(scope="session")
def admin_token() -> str:
    return _make_token(TEST_TENANT, "admin")


@pytest.fixture(scope="session")
def field_token() -> str:
    return _make_token(TEST_TENANT, "field_worker")


@pytest.fixture(scope="session")
def other_tenant_token() -> str:
    """توكن مستأجر مختلف تماماً — يُستخدم لاختبار عزل البيانات."""
    return _make_token(OTHER_TENANT, "admin")
