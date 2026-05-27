#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 Smart Charity SaaS API — v3.0.0
====================================
طبقة SaaS (Software as a Service) مستقلة تعمل فوق النظام الأساسي.

المميزات:
  - Multi-Tenancy: كل جمعية بيانات ومحرك منفصل تماماً
  - API Key Auth: مصادقة عبر X-Tenant-ID + X-API-Key
  - Subscription Plans: Basic / Premium / Enterprise
  - Per-Tenant AI: قواعد الزكاة مخصَّصة لكل جمعية
  - Isolated Logs: سجلات منفصلة لكل مستأجر

التشغيل:
    python -m uvicorn backend.saas_api:saas_app --port 8001 --reload
    # أو بجانب main.py:
    python -m uvicorn backend.saas_api:saas_app --port 8001 &
    python -m uvicorn backend.main:app      --port 8000 &

توثيق API:
    http://localhost:8001/docs
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── تحميل .env ───────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
_env_file = _ROOT / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        for _line in _env_file.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.split("#")[0].strip())

sys.path.insert(0, str(_ROOT))

from smart_charity_ecosystem import (
    Address, ApplicationStatus, Beneficiary, DataPersistence,
    FundType, HijriCalendar, Priority, SectorType,
    SmartCharityEcosystem, UserRole,
)

# ─────────────────────────────────────────────────────────────────────────────
#  ثوابت المنصة
# ─────────────────────────────────────────────────────────────────────────────

TENANTS_DIR = _ROOT / "tenants"

SUBSCRIPTION_PLANS: Dict[str, Dict[str, Any]] = {
    "Basic": {
        "max_monthly_cases":    50,
        "max_beneficiaries":   200,
        "description":         "مناسبة للجمعيات الصغيرة",
    },
    "Premium": {
        "max_monthly_cases":  2_000,
        "max_beneficiaries": 10_000,
        "description":        "للجمعيات متوسطة الحجم",
    },
    "Enterprise": {
        "max_monthly_cases":  float("inf"),
        "max_beneficiaries":  float("inf"),
        "description":        "بدون حدود — للجمعيات الكبرى",
    },
}

# سجل المستأجرين — يُحمَّل من tenants/registry.json عند الإقلاع
_REGISTRY_PATH = TENANTS_DIR / "registry.json"

_DEFAULT_TENANTS: Dict[str, Any] = {
    "riyadh_charity": {
        "name":                "جمعية البر بالرياض",
        "plan":                "Premium",
        "monthly_cases_used":  0,
        "monthly_reset":       datetime.now().strftime("%Y-%m"),
        "api_key":             "key_riyadh_2026",
        "active":              True,
    },
    "jeddah_charity": {
        "name":                "جمعية نفع بجدة",
        "plan":                "Basic",
        "monthly_cases_used":  0,
        "monthly_reset":       datetime.now().strftime("%Y-%m"),
        "api_key":             "key_jeddah_2026",
        "active":              True,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
#  TenantRegistry — إدارة تسجيل المستأجرين
# ─────────────────────────────────────────────────────────────────────────────

class TenantRegistry:
    """سجل مستأجري المنصة — يُحمَّل من الملف ويُحفظ عند كل تغيير."""

    def __init__(self) -> None:
        TENANTS_DIR.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if _REGISTRY_PATH.exists():
            return json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
        self._save(_DEFAULT_TENANTS)
        return dict(_DEFAULT_TENANTS)

    def _save(self, data: Dict[str, Any]) -> None:
        _REGISTRY_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def authenticate(self, tenant_id: str, api_key: str) -> bool:
        t = self._data.get(tenant_id)
        return bool(t and t.get("active") and t.get("api_key") == api_key)

    def get(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        return self._data.get(tenant_id)

    def list_all(self) -> Dict[str, Any]:
        return {tid: {k: v for k, v in info.items() if k != "api_key"}
                for tid, info in self._data.items()}

    def register(self, tenant_id: str, info: Dict[str, Any]) -> None:
        self._data[tenant_id] = info
        self._save(self._data)

    def increment_cases(self, tenant_id: str) -> None:
        now_month = datetime.now().strftime("%Y-%m")
        t = self._data[tenant_id]
        if t.get("monthly_reset") != now_month:
            t["monthly_cases_used"] = 0
            t["monthly_reset"] = now_month
        t["monthly_cases_used"] = t.get("monthly_cases_used", 0) + 1
        self._save(self._data)


# ─────────────────────────────────────────────────────────────────────────────
#  TenantSession — بيئة العمل المعزولة لكل مستأجر
# ─────────────────────────────────────────────────────────────────────────────

_ECO_CACHE: Dict[str, SmartCharityEcosystem] = {}


def _get_tenant_logger(tenant_id: str) -> logging.Logger:
    log_dir = TENANTS_DIR / tenant_id / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    name = f"SaaS.{tenant_id}"
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fh = logging.FileHandler(log_dir / "operations.log", encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger


def _get_eco(tenant_id: str) -> SmartCharityEcosystem:
    """يُرجع (أو يُنشئ) محرك المنظومة الخاص بالمستأجر."""
    if tenant_id in _ECO_CACHE:
        return _ECO_CACHE[tenant_id]

    tenant_dir = TENANTS_DIR / tenant_id
    data_dir = tenant_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    eco = SmartCharityEcosystem()

    data_file = str(data_dir / "charity_data.json")
    persistence = DataPersistence()
    persistence.DATA_FILE = data_file          # عزل ملف البيانات
    ok, _ = persistence.load(eco)
    if not ok:
        eco.load_demo_data()                   # بيانات تجريبية عند الإنشاء الأول

    _ADMIN_ID = f"SAAS-ADMIN-{tenant_id.upper()}"
    if _ADMIN_ID not in eco.governance._users:
        eco.governance._users[_ADMIN_ID] = {
            "user_id":    _ADMIN_ID,
            "name":       "مدير النظام (SaaS)",
            "role":       UserRole.SYSTEM_ADMIN,
            "department": "النظام",
            "created_at": datetime.now().isoformat(),
            "is_active":  True,
        }

    _ECO_CACHE[tenant_id] = eco
    return eco


def _save_eco(tenant_id: str) -> None:
    eco = _ECO_CACHE.get(tenant_id)
    if not eco:
        return
    data_file = str(TENANTS_DIR / tenant_id / "data" / "charity_data.json")
    persistence = DataPersistence()
    persistence.DATA_FILE = data_file
    persistence.save(eco)


# ─────────────────────────────────────────────────────────────────────────────
#  Pydantic Models
# ─────────────────────────────────────────────────────────────────────────────

class TenantRegisterReq(BaseModel):
    tenant_id:   str = Field(..., description="معرّف الجمعية (بالإنجليزية)")
    name:        str = Field(..., description="الاسم العربي للجمعية")
    plan:        str = Field("Basic", description="الباقة: Basic | Premium | Enterprise")
    api_key:     str = Field(..., description="مفتاح API السري")
    admin_secret: str = Field(..., description="كلمة سر مدير المنصة")


class DepositReq(BaseModel):
    fund_type: str   = Field(..., description="نوع الصندوق (قيمة FundType)")
    amount:    float = Field(..., gt=0, description="المبلغ بالريال")
    source:    str   = Field("جهة مجهولة", description="مصدر التبرع")


class CaseProcessReq(BaseModel):
    title:               str   = Field(..., description="عنوان الحالة")
    fund_type:           str   = Field(..., description="نوع الصندوق")
    beneficiary_income:  float = Field(0.0, ge=0, description="الدخل الشهري للمستفيد")
    family_size:         int   = Field(1, ge=1)
    has_disability:      bool  = Field(False)
    amount:              float = Field(..., gt=0, description="المبلغ المطلوب")


class BeneficiaryReq(BaseModel):
    full_name:       str   = Field(..., description="الاسم الكامل")
    national_id:     str   = Field(..., description="رقم الهوية الوطنية")
    phone:           str   = Field(..., description="رقم الجوال")
    city:            str   = Field(..., description="المدينة")
    district:        str   = Field("", description="الحي")
    family_size:     int   = Field(1, ge=1)
    monthly_income:  float = Field(0.0, ge=0)
    has_disability:  bool  = Field(False)


class ApplicationReq(BaseModel):
    beneficiary_id:   str   = Field(..., description="معرّف المستفيد")
    sector:           str   = Field(..., description="القطاع")
    fund_type:        str   = Field(..., description="نوع الصندوق")
    requested_amount: float = Field(..., gt=0)
    description:      str   = Field("", description="وصف الطلب")


# ─────────────────────────────────────────────────────────────────────────────
#  Dependency — التحقق من هوية المستأجر
# ─────────────────────────────────────────────────────────────────────────────

registry = TenantRegistry()
PLATFORM_ADMIN_SECRET = os.getenv("SAAS_ADMIN_SECRET", "saas-admin-secret-2026")


def verify_tenant(
    x_tenant_id: str = Header(..., description="معرّف الجمعية"),
    x_api_key:   str = Header(..., description="مفتاح API السري"),
) -> str:
    if not registry.authenticate(x_tenant_id, x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="فشل التحقق: X-Tenant-ID أو X-API-Key غير صالح",
        )
    return x_tenant_id


def check_plan_limit(tenant_id: str) -> None:
    """يتحقق من حدود الباقة قبل معالجة حالة جديدة."""
    info  = registry.get(tenant_id)
    plan  = SUBSCRIPTION_PLANS.get(info["plan"], SUBSCRIPTION_PLANS["Basic"])
    used  = info.get("monthly_cases_used", 0)
    limit = plan["max_monthly_cases"]
    if limit != float("inf") and used >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"تجاوزت باقة «{info['plan']}» حدها الشهري "
                f"({int(limit)} حالة). يُرجى ترقية الباقة."
            ),
        )


# ─────────────────────────────────────────────────────────────────────────────
#  FastAPI App
# ─────────────────────────────────────────────────────────────────────────────

saas_app = FastAPI(
    title="Smart Charity SaaS API",
    description="منصة خيرية سحابية متعددة المستأجرين — v3.0.0",
    version="3.0.0",
    docs_url="/docs",
)

saas_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── نقطة الدخول ──────────────────────────────────────────────────────────────

@saas_app.get("/", tags=["المنصة"])
def root():
    today = HijriCalendar.today_dual()
    return {
        "status":   "ONLINE",
        "platform": "Smart Charity SaaS — منظومة الخير الذكية السحابية",
        "version":  "3.0.0",
        "date":     today,
        "features": ["Multi-Tenancy", "AI Eligibility", "Isolated Financials",
                     "Subscription Plans", "Full Lifecycle"],
        "tenants_active": len([t for t in registry.list_all().values() if t.get("active")]),
    }


# ── إدارة المستأجرين (Admin) ──────────────────────────────────────────────────

@saas_app.post("/api/v1/tenants", tags=["إدارة المنصة"], status_code=201)
def register_tenant(data: TenantRegisterReq):
    """تسجيل جمعية جديدة كمستأجر في المنصة (يتطلب admin_secret)."""
    if data.admin_secret != PLATFORM_ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="كلمة سر المدير غير صحيحة")
    if registry.get(data.tenant_id):
        raise HTTPException(status_code=409, detail="المعرّف مستخدم مسبقاً")
    if data.plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail=f"الباقة غير صالحة. الخيارات: {list(SUBSCRIPTION_PLANS)}")

    registry.register(data.tenant_id, {
        "name":               data.name,
        "plan":               data.plan,
        "monthly_cases_used": 0,
        "monthly_reset":      datetime.now().strftime("%Y-%m"),
        "api_key":            data.api_key,
        "active":             True,
        "registered_at":      datetime.now().isoformat(),
    })
    _get_eco(data.tenant_id)   # تهيئة بيئة المستأجر فوراً
    return {"message": f"تم تسجيل الجمعية «{data.name}» بنجاح", "tenant_id": data.tenant_id}


@saas_app.get("/api/v1/tenants", tags=["إدارة المنصة"])
def list_tenants(admin_secret: str = ""):
    """قائمة جميع المستأجرين (بدون API Keys)."""
    if admin_secret != PLATFORM_ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="غير مصرح")
    return registry.list_all()


# ── لوحة التحكم ──────────────────────────────────────────────────────────────

@saas_app.get("/api/v1/dashboard", tags=["لوحة التحكم"])
def tenant_dashboard(tenant_id: str = Depends(verify_tenant)):
    eco  = _get_eco(tenant_id)
    info = registry.get(tenant_id)
    plan = SUBSCRIPTION_PLANS[info["plan"]]
    used = info.get("monthly_cases_used", 0)
    limit = plan["max_monthly_cases"]

    apps  = list(eco._all_applications.values())
    bens  = list(eco._beneficiaries.values())
    today = HijriCalendar.today_dual()

    return {
        "tenant":  info["name"],
        "plan":    info["plan"],
        "date":    today,
        "usage": {
            "cases_this_month": used,
            "limit":            limit if limit != float("inf") else "غير محدود",
            "remaining":        max(0, limit - used) if limit != float("inf") else "غير محدود",
        },
        "stats": {
            "beneficiaries":   len(bens),
            "applications":    len(apps),
            "pending":         sum(1 for a in apps if a.status == ApplicationStatus.SUBMITTED),
            "approved":        sum(1 for a in apps if a.status == ApplicationStatus.APPROVED),
            "disbursed":       sum(1 for a in apps if a.status == ApplicationStatus.DISBURSED),
        },
        "balances": {
            ft.value: eco.finance.get_balance(ft) for ft in FundType
        },
    }


# ── المستفيدون ───────────────────────────────────────────────────────────────

@saas_app.get("/api/v1/beneficiaries", tags=["المستفيدون"])
def list_beneficiaries(
    limit: int = 50,
    tenant_id: str = Depends(verify_tenant),
):
    eco = _get_eco(tenant_id)
    bens = [b for b in eco._beneficiaries.values() if not b.is_archived]
    return {"count": len(bens), "beneficiaries": [
        {
            "id":       b.beneficiary_id,
            "name":     b.full_name,
            "city":     b.address.city,
            "income":   b.monthly_income,
            "family":   b.family_size,
            "eligible": b.is_eligible,
            "category": b.zakat_category.value if b.zakat_category else None,
        }
        for b in bens[:limit]
    ]}


@saas_app.post("/api/v1/beneficiaries", tags=["المستفيدون"], status_code=201)
def add_beneficiary(data: BeneficiaryReq, tenant_id: str = Depends(verify_tenant)):
    eco = _get_eco(tenant_id)
    info = registry.get(tenant_id)
    plan = SUBSCRIPTION_PLANS[info["plan"]]
    if len(eco._beneficiaries) >= plan["max_beneficiaries"]:
        raise HTTPException(403, f"وصلت لحد المستفيدين في باقة «{info['plan']}»")

    b, msg = eco.register_beneficiary(
        full_name=data.full_name,
        national_id=data.national_id,
        phone=data.phone,
        city=data.city,
        district=data.district,
        family_size=data.family_size,
        monthly_income=data.monthly_income,
        has_disability=data.has_disability,
    )
    _save_eco(tenant_id)
    return {"message": msg, "beneficiary_id": b.beneficiary_id, "eligible": b.is_eligible}


# ── الطلبات ──────────────────────────────────────────────────────────────────

@saas_app.get("/api/v1/applications", tags=["الطلبات"])
def list_applications(
    status_filter: str = "",
    limit: int = 50,
    tenant_id: str = Depends(verify_tenant),
):
    eco  = _get_eco(tenant_id)
    apps = list(eco._all_applications.values())
    if status_filter:
        apps = [a for a in apps if a.status.value == status_filter]
    return [
        {
            "id":          a.application_id,
            "beneficiary": a.beneficiary_id,
            "sector":      a.sector.value,
            "fund":        a.fund_type.value,
            "amount":      a.requested_amount,
            "status":      a.status.value,
            "date":        str(a.submission_date),
        }
        for a in sorted(apps, key=lambda x: x.submission_date, reverse=True)[:limit]
    ]


@saas_app.post("/api/v1/applications", tags=["الطلبات"], status_code=201)
def submit_application(data: ApplicationReq, tenant_id: str = Depends(verify_tenant)):
    eco = _get_eco(tenant_id)
    try:
        sector    = SectorType(data.sector)
        fund_type = FundType(data.fund_type)
    except ValueError as e:
        raise HTTPException(400, str(e))

    app_obj, msg = eco.submit_application(
        beneficiary_id=data.beneficiary_id,
        sector=sector,
        fund_type=fund_type,
        requested_amount=data.requested_amount,
        description=data.description,
    )
    _save_eco(tenant_id)
    return {"message": msg, "application_id": app_obj.application_id, "status": app_obj.status.value}


@saas_app.post("/api/v1/applications/{app_id}/approve", tags=["الطلبات"])
def approve_application(
    app_id:          str,
    approved_amount: float,
    notes:           str = "",
    tenant_id:       str = Depends(verify_tenant),
):
    eco     = _get_eco(tenant_id)
    admin   = f"SAAS-ADMIN-{tenant_id.upper()}"
    ok, msg = eco.process_approval(app_id, admin, approved_amount, notes)
    if not ok:
        raise HTTPException(400, msg)
    _save_eco(tenant_id)
    return {"message": msg, "application_id": app_id}


@saas_app.post("/api/v1/applications/{app_id}/disburse", tags=["الطلبات"])
def disburse_application(app_id: str, tenant_id: str = Depends(verify_tenant)):
    eco     = _get_eco(tenant_id)
    admin   = f"SAAS-ADMIN-{tenant_id.upper()}"
    ok, msg = eco.process_disbursement(app_id, admin)
    if not ok:
        raise HTTPException(400, msg)
    _save_eco(tenant_id)
    return {"message": msg, "application_id": app_id}


# ── النظام المالي ─────────────────────────────────────────────────────────────

@saas_app.post("/api/v1/financial/deposit", tags=["النظام المالي"])
def deposit_funds(data: DepositReq, tenant_id: str = Depends(verify_tenant)):
    eco = _get_eco(tenant_id)
    ok  = eco.finance.add_fund(data.fund_type, data.amount, data.source)
    if not ok:
        raise HTTPException(400, f"نوع الصندوق غير صالح: {data.fund_type}")
    _save_eco(tenant_id)
    logger = _get_tenant_logger(tenant_id)
    logger.info("إيداع %.2f في صندوق %s من %s", data.amount, data.fund_type, data.source)
    try:
        ft = FundType(data.fund_type)
        new_bal = eco.finance.get_balance(ft)
    except ValueError:
        new_bal = None
    return {
        "message":     "تم الإيداع بنجاح",
        "fund":        data.fund_type,
        "deposited":   data.amount,
        "new_balance": new_bal,
    }


@saas_app.get("/api/v1/financial/balances", tags=["النظام المالي"])
def get_balances(tenant_id: str = Depends(verify_tenant)):
    eco = _get_eco(tenant_id)
    return {ft.value: eco.finance.get_balance(ft) for ft in FundType}


# ── معالجة الحالات (AI + صرف + أرشفة في خطوة واحدة) ──────────────────────────

@saas_app.post("/api/v1/cases/process", tags=["المعالجة الذكية"])
def process_case(data: CaseProcessReq, tenant_id: str = Depends(verify_tenant)):
    """
    تقييم الحالة بالذكاء الاصطناعي → خصم المبلغ → أرشفة القرار — خطوة واحدة.
    يُحسَب في كوتا الباقة الشهرية.
    """
    check_plan_limit(tenant_id)
    eco    = _get_eco(tenant_id)
    logger = _get_tenant_logger(tenant_id)

    # 1. تقييم الأهلية بالذكاء الاصطناعي
    evaluation = eco.ai.evaluate_eligibility({
        "beneficiary_income": data.beneficiary_income,
        "family_size":        data.family_size,
        "has_disability":     data.has_disability,
        "fund_type":          data.fund_type,
    })

    if not evaluation["is_eligible"]:
        logger.warning("رفض حالة: %s — %s", data.title, evaluation["reason"])
        return {
            "status":         "REJECTED",
            "reason":         evaluation["reason"],
            "confidence":     evaluation["confidence_level"],
        }

    # 2. خصم المبلغ من الصندوق
    ok = eco.finance.deduct_fund(data.fund_type, data.amount, data.title)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail=f"رصيد غير كافٍ في صندوق «{data.fund_type}» أو الصندوق غير معرَّف",
        )

    # 3. تسجيل القرار في سجل الحوكمة
    decision_id = eco.governance.record_decision({
        "application_id": f"CASE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "amount":         data.amount,
        "action":         f"معالجة حالة: {data.title}",
    })

    # 4. تحديث كوتا الباقة
    registry.increment_cases(tenant_id)
    _save_eco(tenant_id)
    logger.info("حالة مُعتمدة: %s | قرار: %s | مبلغ: %.2f", data.title, decision_id, data.amount)

    try:
        ft      = FundType(data.fund_type)
        new_bal = eco.finance.get_balance(ft)
    except ValueError:
        new_bal = None

    return {
        "status":      "APPROVED_AND_EXECUTED",
        "decision_id": decision_id,
        "ai": {
            "eligible":   evaluation["is_eligible"],
            "confidence": evaluation["confidence_level"],
            "reason":     evaluation["reason"],
        },
        "financial": {
            "deducted":        data.amount,
            "remaining_balance": new_bal,
        },
    }


# ── تقارير وإحصاءات ──────────────────────────────────────────────────────────

@saas_app.get("/api/v1/reports/usage", tags=["التقارير"])
def usage_report(tenant_id: str = Depends(verify_tenant)):
    """تقرير استخدام الباقة الشهرية."""
    info  = registry.get(tenant_id)
    plan  = SUBSCRIPTION_PLANS[info["plan"]]
    used  = info.get("monthly_cases_used", 0)
    limit = plan["max_monthly_cases"]
    return {
        "tenant":       info["name"],
        "plan":         info["plan"],
        "plan_details": plan["description"],
        "month":        info.get("monthly_reset", ""),
        "cases_used":   used,
        "cases_limit":  limit if limit != float("inf") else "غير محدود",
        "percent_used": round(used / limit * 100, 1) if limit != float("inf") and limit > 0 else 0,
    }


@saas_app.get("/api/v1/reports/audit", tags=["التقارير"])
def audit_log(limit: int = 20, tenant_id: str = Depends(verify_tenant)):
    """سجل التدقيق الخاص بالمستأجر."""
    eco = _get_eco(tenant_id)
    return eco.governance.get_audit_log(limit)


@saas_app.get("/api/v1/ai/evaluate", tags=["الذكاء الاصطناعي"])
def ai_evaluate(
    income:       float = 0.0,
    family_size:  int   = 1,
    has_disability: bool = False,
    fund_type:    str   = "الزكاة",
    tenant_id:    str   = Depends(verify_tenant),
):
    """تقييم أهلية حالة بالذكاء الاصطناعي بدون صرف."""
    eco = _get_eco(tenant_id)
    return eco.ai.evaluate_eligibility({
        "beneficiary_income": income,
        "family_size":        family_size,
        "has_disability":     has_disability,
        "fund_type":          fund_type,
    })


# ─────────────────────────────────────────────────────────────────────────────
#  تشغيل مباشر
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 Smart Charity SaaS API — v3.0.0")
    print("   http://127.0.0.1:8001")
    print("   http://127.0.0.1:8001/docs")
    print("=" * 60)
    uvicorn.run(saas_app, host="127.0.0.1", port=8001)
