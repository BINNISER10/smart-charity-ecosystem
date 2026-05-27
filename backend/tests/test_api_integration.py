"""
test_api_integration.py — Integration Tests للـ SaaS API
يختبر:
  1. صحة الـ API (health)
  2. مسار Login الصحيح والخاطئ
  3. رفض الطلبات بدون توكن / توكن مزيف
  4. المسار الكامل Fast-Track (register → submit → auto-disburse)
  5. عزل المستأجرين (Tenant Isolation)

يستخدم httpx.AsyncClient + ASGITransport (لا يحتاج سيرفر حقيقي)
"""
from __future__ import annotations

import pytest
import httpx
from httpx import ASGITransport

from conftest import TEST_TENANT, OTHER_TENANT  # مُعرَّفان في conftest.py


# ── Fixture: مثيل HTTP Client ────────────────────────────────────────────────
@pytest.fixture
async def client():
    """
    ينشئ AsyncClient يتصل مباشرة بـ FastAPI App بدون شبكة حقيقية.
    يُنظِّف حالة المستأجر المؤقت قبل كل اختبار.
    """
    from main import app  # يُستورد هنا بعد ضبط sys.path في conftest
    from core import evict_eco

    evict_eco(TEST_TENANT)    # بداية نظيفة لكل اختبار
    evict_eco(OTHER_TENANT)

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ════════════════════════════════════════════════════════════════════════════════
#  مجموعة 1: صحة الـ API
# ════════════════════════════════════════════════════════════════════════════════

async def test_openapi_reachable(client: httpx.AsyncClient):
    """الـ API يستجيب ويقدم مخطط OpenAPI."""
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    assert "openapi" in resp.json()


# ════════════════════════════════════════════════════════════════════════════════
#  مجموعة 2: Authentication
# ════════════════════════════════════════════════════════════════════════════════

async def test_login_valid_admin(client: httpx.AsyncClient):
    """بيانات صحيحة → JWT يحتوي tenant_id و role."""
    resp = await client.post("/api/v1/auth/login", json={
        "username":  "admin@org_a",
        "password":  "admin123",
        "tenant_id": "org_a",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["tenant_id"] == "org_a"
    assert data["role"]      == "admin"


async def test_login_wrong_password(client: httpx.AsyncClient):
    """كلمة مرور خاطئة → 401."""
    resp = await client.post("/api/v1/auth/login", json={
        "username":  "admin@org_a",
        "password":  "WRONG_PASSWORD",
        "tenant_id": "org_a",
    })
    assert resp.status_code == 401


async def test_login_unknown_user(client: httpx.AsyncClient):
    """مستخدم غير موجود → 401."""
    resp = await client.post("/api/v1/auth/login", json={
        "username":  "ghost@org_a",
        "password":  "anything",
        "tenant_id": "org_a",
    })
    assert resp.status_code == 401


# ════════════════════════════════════════════════════════════════════════════════
#  مجموعة 3: التحقق من الـ Authorization Header
# ════════════════════════════════════════════════════════════════════════════════

async def test_submit_no_auth_header(client: httpx.AsyncClient):
    """بدون Authorization → 403 (FastAPI Depends يرفع مباشرة)."""
    resp = await client.post("/api/v1/applications/submit", json={
        "beneficiary_id":   "BEN-FAKE",
        "sector":           "الصحة",
        "requested_amount": 1000,
        "fund_type":        "الزكاة",
        "description":      "test",
    })
    assert resp.status_code == 403


async def test_submit_invalid_jwt(client: httpx.AsyncClient):
    """توكن JWT مزيف → 401."""
    resp = await client.post(
        "/api/v1/applications/submit",
        json={
            "beneficiary_id":   "BEN-FAKE",
            "sector":           "الصحة",
            "requested_amount": 1000,
            "fund_type":        "الزكاة",
            "description":      "test",
        },
        headers={"Authorization": "Bearer FAKE.JWT.TOKEN"},
    )
    assert resp.status_code == 401


async def test_beneficiaries_no_auth(client: httpx.AsyncClient):
    """قائمة المستفيدين بدون توكن → 403."""
    resp = await client.get("/api/v1/beneficiaries")
    assert resp.status_code == 403


# ════════════════════════════════════════════════════════════════════════════════
#  مجموعة 4: Fast-Track — المسار الكامل عبر الـ API
# ════════════════════════════════════════════════════════════════════════════════

async def test_fast_track_full_flow(
    client: httpx.AsyncClient,
    admin_token: str,
) -> None:
    """
    مسار كامل:
      1. تمويل رصيد الزكاة للمستأجر
      2. تسجيل مستفيد بحاجة ماسة (income=0, disability=True, family=8)
      3. تقديم طلب صحي حرج بمبلغ ≤ FAST_TRACK_LIMIT (5000)
      4. التحقق من أن fast_tracked=True وstatus=تم الصرف
    """
    from core import get_eco
    from smart_charity_ecosystem import FundType

    # 1. بذر الرصيد مسبقاً (لا يوجد endpoint لذلك حالياً)
    eco = get_eco(TEST_TENANT)
    eco.finance._balances[FundType.ZAKAT] = 50_000.0

    headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. تسجيل مستفيد
    ben_resp = await client.post(
        "/api/v1/beneficiaries",
        json={
            "full_name":      "اختبار المسار السريع CI",
            "national_id":    "1099988877",
            "phone":          "0599998877",
            "city":           "الرياض",
            "district":       "التكامل",
            "family_size":    8,
            "monthly_income": 0.0,
            "is_employed":    False,
            "has_disability": True,
            "field_notes":    "مريض مزمن فاقد الدخل — حالة طوارئ طبية",
        },
        headers=headers,
    )
    assert ben_resp.status_code == 201, f"فشل تسجيل المستفيد: {ben_resp.text}"
    ben_data = ben_resp.json()
    assert "beneficiary_id" in ben_data
    ben_id = ben_data["beneficiary_id"]

    # 3. تقديم طلب صحي حرج بمبلغ أقل من حد المسار السريع
    app_resp = await client.post(
        "/api/v1/applications/submit",
        json={
            "beneficiary_id":   ben_id,
            "sector":           "الصحة",
            "requested_amount": 2500.0,
            "fund_type":        "الزكاة",
            "description":      "علاج طارئ — غسيل كلى أسبوعي",
        },
        headers=headers,
    )
    assert app_resp.status_code == 201, f"فشل تقديم الطلب: {app_resp.text}"
    app_data = app_resp.json()

    # 4. التحقق من تفعيل المسار السريع
    assert app_data.get("fast_tracked") is True, (
        f"المسار السريع لم يُفعَّل!\n"
        f"الأولوية: {app_data.get('priority')}\n"
        f"الحالة:   {app_data.get('status')}\n"
        f"Response: {app_data}"
    )
    assert "صرف" in app_data.get("status", ""), (
        f"الحالة المتوقعة: 'تم الصرف' — الفعلية: {app_data.get('status')}"
    )


async def test_fast_track_not_triggered_high_amount(
    client: httpx.AsyncClient,
    admin_token: str,
) -> None:
    """مبلغ > 5000 (FAST_TRACK_LIMIT) لا يُفعِّل المسار السريع."""
    from core import get_eco
    from smart_charity_ecosystem import FundType

    eco = get_eco(TEST_TENANT)
    eco.finance._balances[FundType.ZAKAT] = 100_000.0

    headers = {"Authorization": f"Bearer {admin_token}"}

    # تسجيل مستفيد
    ben_resp = await client.post(
        "/api/v1/beneficiaries",
        json={
            "full_name":      "اختبار مبلغ كبير CI",
            "national_id":    "1077766655",
            "phone":          "0577766655",
            "city":           "جدة",
            "district":       "التكامل",
            "family_size":    6,
            "monthly_income": 0.0,
            "is_employed":    False,
            "has_disability": True,
            "field_notes":    "يحتاج سكن وعلاج",
        },
        headers=headers,
    )
    assert ben_resp.status_code == 201
    ben_id = ben_resp.json()["beneficiary_id"]

    # طلب بمبلغ أعلى من حد المسار السريع
    app_resp = await client.post(
        "/api/v1/applications/submit",
        json={
            "beneficiary_id":   ben_id,
            "sector":           "الإسكان",
            "requested_amount": 15_000.0,
            "fund_type":        "الزكاة",
            "description":      "إعادة تأهيل السكن",
        },
        headers=headers,
    )
    assert app_resp.status_code == 201
    app_data = app_resp.json()
    # المبلغ > FAST_TRACK_LIMIT → لا مسار سريع
    assert app_data.get("fast_tracked") is False, (
        f"المسار السريع فُعِّل خطأً لمبلغ {15_000}: {app_data}"
    )


# ════════════════════════════════════════════════════════════════════════════════
#  مجموعة 5: Tenant Isolation
# ════════════════════════════════════════════════════════════════════════════════

async def test_tenant_isolation(
    client: httpx.AsyncClient,
    admin_token: str,
    other_tenant_token: str,
) -> None:
    """
    المستأجر A يرى بياناته فقط.
    المستأجر B لا يرى أي بيانات لـ A.
    """
    headers_a = {"Authorization": f"Bearer {admin_token}"}
    headers_b = {"Authorization": f"Bearer {other_tenant_token}"}

    # تسجيل مستفيد في A
    ben_resp = await client.post(
        "/api/v1/beneficiaries",
        json={
            "full_name":      "مستفيد خاص بـ A",
            "national_id":    "1055544433",
            "phone":          "0555544433",
            "city":           "الدمام",
            "district":       "العزل",
            "family_size":    4,
            "monthly_income": 1000.0,
            "is_employed":    True,
            "has_disability": False,
        },
        headers=headers_a,
    )
    assert ben_resp.status_code == 201
    ben_id_a = ben_resp.json()["beneficiary_id"]

    # المستأجر B يحاول الوصول لقائمة المستفيدين
    list_b = await client.get("/api/v1/beneficiaries", headers=headers_b)
    assert list_b.status_code == 200

    ids_b = {b["beneficiary_id"] for b in list_b.json()}
    assert ben_id_a not in ids_b, (
        f"انتهاك عزل المستأجرين! "
        f"المستفيد {ben_id_a} الخاص بـ '{TEST_TENANT}' "
        f"ظهر في قائمة '{OTHER_TENANT}'"
    )

    # المستأجر B يحاول جلب مستفيد A مباشرة → 404
    direct = await client.get(
        f"/api/v1/beneficiaries/{ben_id_a}",
        headers=headers_b,
    )
    assert direct.status_code == 404, (
        f"المستأجر B استطاع قراءة مستفيد لـ A! (status={direct.status_code})"
    )
