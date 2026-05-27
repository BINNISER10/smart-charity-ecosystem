#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Backend — Smart Charity Ecosystem
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── تحميل .env ──────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
_env_file = _ROOT / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_file)
    except ImportError:
        # dotenv غير مثبت — نقرأ .env يدوياً (stdlib only)
        for _line in _env_file.read_text(encoding="utf-8").splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.split("#")[0].strip())

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                  # backend/

from smart_charity_ecosystem import (
    Address, Application, ApplicationStatus, Beneficiary,
    DataPersistence, FundType, HijriCalendar, Priority,
    SectorType, SmartAI, SmartCharityEcosystem,
    Transaction, UserRole, ZakatCategory,
)

# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Charity Ecosystem API",
    description="واجهة برمجية لمنظومة العمل الخيري الذكي",
    version="1.0.0",
)

_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
_ORIGINS = [o.strip() for o in _origins_raw.split(",")] if _origins_raw != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

eco         = SmartCharityEcosystem()
persistence = DataPersistence()


API_ADMIN_ID = os.getenv("API_ADMIN_ID", "API-ADMIN")


def _ensure_api_admin() -> None:
    """يضمن وجود مستخدم النظام الإداري دائماً — ضروري لعمل نقاط الموافقة."""
    if API_ADMIN_ID not in eco.governance._users:
        eco.governance._users[API_ADMIN_ID] = {
            "user_id":    API_ADMIN_ID,
            "name":       "مدير النظام (API)",
            "role":       UserRole.SYSTEM_ADMIN,
            "department": "النظام",
            "created_at": datetime.now().isoformat(),
            "is_active":  True,
        }


@app.on_event("startup")
async def _startup() -> None:
    ok, _ = persistence.load(eco)
    if not ok:
        eco.load_demo_data()
    _ensure_api_admin()
    _seed_ai_history()


def _seed_ai_history() -> None:
    """تغذية الذكاء الاصطناعي بالتاريخ المحفوظ في data/history.json عند الإقلاع."""
    import json as _json, pathlib as _pl
    _hist = _pl.Path(__file__).resolve().parent.parent / "data" / "history.json"
    if not _hist.exists():
        return
    try:
        data = _json.loads(_hist.read_text(encoding="utf-8"))
        entries = data.get("history", [])
        for e in entries:
            eco.ai._experience_db.append({
                "application_id":    e.get("id", ""),
                "sector":            e.get("sector", ""),
                "score":             float(e.get("ai_score", 50)),
                "priority":          "MEDIUM",
                "income_per_capita": 0,
                "family_size":       1,
                "has_disability":    False,
                "timestamp":         e.get("date", ""),
            })
    except Exception:
        pass


# ── Serialisers ───────────────────────────────────────────────────────────────

def _ben(b: Beneficiary) -> Dict[str, Any]:
    return {
        "id":                  b.beneficiary_id,
        "name":                b.full_name,
        "national_id":         b.national_id,
        "phone":               b.phone,
        "city":                b.address.city,
        "district":            b.address.district,
        "family_size":         b.family_size,
        "monthly_income":      b.monthly_income,
        "is_employed":         b.is_employed,
        "has_disability":      b.has_disability,
        "is_eligible":         b.is_eligible,
        "eligibility_notes":   b.eligibility_notes,
        "zakat_category":      b.zakat_category.value if b.zakat_category else None,
        "registration_date":   str(b.registration_date),
        "registration_date_h": HijriCalendar.format_hijri(
            b.registration_date.year, b.registration_date.month, b.registration_date.day
        ),
        "is_archived": b.is_archived,
    }


def _app(a: Application) -> Dict[str, Any]:
    return {
        "id":                a.application_id,
        "beneficiary_id":    a.beneficiary_id,
        "sector":            a.sector.value,
        "fund_type":         a.fund_type.value,
        "requested_amount":  a.requested_amount,
        "approved_amount":   a.approved_amount,
        "status":            a.status.value,
        "priority":          a.priority.name,
        "description":       a.description,
        "supporting_docs":   a.supporting_docs,
        "ai_score":          a.ai_score,
        "ai_recommendation": a.ai_recommendation,
        "submission_date":   str(a.submission_date),
        "submission_date_h": HijriCalendar.format_hijri(
            a.submission_date.year, a.submission_date.month, a.submission_date.day
        ),
        "approval_date": str(a.approval_date) if a.approval_date else None,
        "approver_id":   a.approver_id,
        "audit_trail":   a.audit_trail,
    }


def _txn(t: Transaction) -> Dict[str, Any]:
    return {
        "id":            t.transaction_id,
        "fund_type":     t.fund_type.value,
        "amount":        t.amount,
        "type":          t.transaction_type,
        "reference_id":  t.reference_id,
        "description":   t.description,
        "executor_id":   t.executor_id,
        "balance_after": t.balance_after,
        "timestamp":     t.timestamp.isoformat(),
    }


# ── Pydantic request models ────────────────────────────────────────────────────

class BeneficiaryCreate(BaseModel):
    name: str
    national_id: str
    phone: str
    city: str = "الرياض"
    district: str = ""
    family_size: int = 4
    monthly_income: float = 0.0
    is_employed: bool = False
    has_disability: bool = False


class ApplicationCreate(BaseModel):
    beneficiary_id: str
    sector: str
    fund_type: str
    requested_amount: float
    description: str
    supporting_docs: List[str] = []


class ApproveReq(BaseModel):
    approver_id: str
    approved_amount: float
    notes: str = ""


class RejectReq(BaseModel):
    rejector_id: str
    reason: str


class CancelReq(BaseModel):
    canceller_id: str
    reason: str = ""


class DisburseReq(BaseModel):
    executor_id: str = "API-ADMIN"


class DonateReq(BaseModel):
    donor_name: str
    donor_phone: str
    amount: float
    fund_type: str


class ZakatReq(BaseModel):
    cash: float = 0.0
    trade_goods: float = 0.0
    gold_grams: float = 0.0
    silver_grams: float = 0.0
    crops_kg: float = 0.0
    irrigated: bool = False
    camels: int = 0
    cattle: int = 0
    sheep: int = 0


class BeneficiaryUpdate(BaseModel):
    name:           Optional[str]   = None
    phone:          Optional[str]   = None
    national_id:    Optional[str]   = None
    city:           Optional[str]   = None
    district:       Optional[str]   = None
    family_size:    Optional[int]   = None
    monthly_income: Optional[float] = None
    has_disability: Optional[bool]  = None


class ApplicationUpdate(BaseModel):
    description:      Optional[str]   = None
    requested_amount: Optional[float] = None
    priority:         Optional[str]   = None


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.get("/api/dashboard")
def dashboard() -> Dict[str, Any]:
    today  = date.today()
    report = eco.get_ecosystem_report()
    fin    = eco.finance.get_financial_report()

    status_dist: Dict[str, int] = {}
    sector_spend: Dict[str, float] = {}
    for a in eco._all_applications.values():
        status_dist[a.status.value] = status_dist.get(a.status.value, 0) + 1
        if a.approved_amount > 0 and a.status in (
            ApplicationStatus.APPROVED, ApplicationStatus.DISBURSED
        ):
            sector_spend[a.sector.value] = (
                sector_spend.get(a.sector.value, 0.0) + a.approved_amount
            )

    pending = sum(
        1 for a in eco._all_applications.values()
        if a.status in {
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.AI_ANALYZED,
            ApplicationStatus.PENDING_APPROVAL,
        }
    )

    return {
        "date": {
            "gregorian": today.strftime("%Y/%m/%d"),
            "hijri":     HijriCalendar.format_hijri(today.year, today.month, today.day),
            "dual":      HijriCalendar.today_dual(),
        },
        "stats": {
            "total_beneficiaries":    report["total_beneficiaries"],
            "eligible_beneficiaries": report["eligible_beneficiaries"],
            "total_applications":     report["total_applications"],
            "pending_applications":   pending,
            "total_received":         fin["total_received"],
            "total_disbursed":        fin["total_disbursed"],
            "total_donors":           fin["total_donors"],
        },
        "status_distribution":  status_dist,
        "sector_spending":      sector_spend,
        "fund_balances":        {f.value: eco.finance.get_balance(f) for f in FundType},
        "recent_transactions":  [_txn(t) for t in reversed(eco.finance.get_transactions(limit=5))],
        "sector_kpis":          report["sector_kpis"],
    }


# ── Beneficiaries ─────────────────────────────────────────────────────────────

@app.get("/api/beneficiaries")
def list_beneficiaries(search: str = "", include_archived: bool = False):
    bens = list(eco._beneficiaries.values())
    if not include_archived:
        bens = [b for b in bens if not b.is_archived]
    if search:
        q = search.lower()
        bens = [
            b for b in bens
            if q in b.full_name.lower()
            or q in b.national_id
            or q in b.beneficiary_id.lower()
        ]
    return [_ben(b) for b in bens]


@app.post("/api/beneficiaries", status_code=201)
def create_beneficiary(data: BeneficiaryCreate):
    b = Beneficiary(
        full_name=data.name,
        national_id=data.national_id,
        phone=data.phone,
        address=Address(city=data.city, district=data.district),
        family_size=data.family_size,
        monthly_income=data.monthly_income,
        is_employed=data.is_employed,
        has_disability=data.has_disability,
    )
    is_eligible, reason = eco.register_beneficiary(b)
    persistence.save(eco)
    return {"beneficiary": _ben(b), "is_eligible": is_eligible, "reason": reason}


@app.get("/api/beneficiaries/{ben_id}")
def get_beneficiary(ben_id: str):
    hist = eco.get_beneficiary_history(ben_id)
    if not hist["beneficiary"]:
        raise HTTPException(404, "المستفيد غير موجود")
    return {
        "beneficiary":     _ben(hist["beneficiary"]),
        "applications":    [_app(a) for a in hist["applications"]],
        "total_disbursed": hist["total_disbursed"],
        "disbursed_count": hist["disbursed_count"],
        "last_activity":   str(hist["last_activity"]) if hist["last_activity"] else None,
    }


@app.post("/api/beneficiaries/{ben_id}/archive")
def archive_beneficiary(ben_id: str):
    if not eco.archive_beneficiary(ben_id, "API"):
        raise HTTPException(404, "المستفيد غير موجود")
    persistence.save(eco)
    return {"success": True}


@app.post("/api/beneficiaries/{ben_id}/restore")
def restore_beneficiary(ben_id: str):
    if not eco.restore_beneficiary(ben_id, "API"):
        raise HTTPException(404, "المستفيد غير موجود")
    persistence.save(eco)
    return {"success": True}


@app.patch("/api/beneficiaries/{ben_id}")
def update_beneficiary(ben_id: str, data: BeneficiaryUpdate):
    b = eco._beneficiaries.get(ben_id)
    if not b:
        raise HTTPException(404, "المستفيد غير موجود")
    if data.name           is not None: b.full_name          = data.name
    if data.phone          is not None: b.phone              = data.phone
    if data.national_id    is not None: b.national_id        = data.national_id
    if data.city           is not None: b.address.city       = data.city
    if data.district       is not None: b.address.district   = data.district
    if data.family_size    is not None: b.family_size        = max(1, data.family_size)
    if data.monthly_income is not None: b.monthly_income     = max(0.0, data.monthly_income)
    if data.has_disability is not None: b.has_disability     = data.has_disability
    is_elig, reason = eco.ai.check_eligibility(b)
    b.is_eligible       = is_elig
    b.eligibility_notes = reason
    eco.governance._record_audit(
        action="BENEFICIARY_EDITED",
        actor="API",
        details=f"تعديل بيانات: {b.full_name} [{ben_id}]",
    )
    persistence.save(eco)
    return {"beneficiary": _ben(b), "is_eligible": is_elig, "reason": reason}


@app.patch("/api/applications/{app_id}")
def update_application(app_id: str, data: ApplicationUpdate):
    a = eco._all_applications.get(app_id)
    if not a:
        raise HTTPException(404, "الطلب غير موجود")
    if data.description is not None:
        a.description = data.description
    EDITABLE_STATUSES = {ApplicationStatus.SUBMITTED, ApplicationStatus.AI_ANALYZED}
    if data.requested_amount is not None:
        if a.status not in EDITABLE_STATUSES:
            raise HTTPException(400, "لا يمكن تعديل المبلغ بعد بدء المعالجة")
        a.requested_amount = max(0.0, data.requested_amount)
    if data.priority is not None:
        try:
            a.priority = Priority[data.priority]
        except KeyError:
            try:
                a.priority = Priority(data.priority)
            except ValueError:
                raise HTTPException(400, f"قيمة الأولوية غير صالحة: {data.priority}")
    eco.governance._record_audit(
        action="APPLICATION_EDITED",
        actor="API",
        details=f"تعديل طلب: {app_id}",
    )
    persistence.save(eco)
    return {"application": _app(a)}


# ── Applications ──────────────────────────────────────────────────────────────

@app.get("/api/applications")
def list_applications(status: str = "", sector: str = "", limit: int = 100):
    apps = list(eco._all_applications.values())
    if status:
        apps = [a for a in apps if a.status.value == status]
    if sector:
        apps = [a for a in apps if a.sector.value == sector]
    apps.sort(key=lambda a: a.submission_date, reverse=True)
    return [_app(a) for a in apps[:limit]]


@app.get("/api/applications/{app_id}")
def get_application(app_id: str):
    a = eco._all_applications.get(app_id)
    if not a:
        raise HTTPException(404, "الطلب غير موجود")
    return {"application": _app(a)}


@app.post("/api/applications", status_code=201)
def create_application(data: ApplicationCreate):
    try:
        sector_type = SectorType(data.sector)
        fund_type   = FundType(data.fund_type)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    app_obj = Application(
        beneficiary_id=data.beneficiary_id,
        sector=sector_type,
        fund_type=fund_type,
        requested_amount=data.requested_amount,
        description=data.description,
        supporting_docs=data.supporting_docs,
    )
    ok, msg = eco.submit_application(app_obj)
    if not ok:
        raise HTTPException(400, msg)
    persistence.save(eco)
    return {"application": _app(app_obj), "message": msg}


@app.post("/api/applications/{app_id}/approve")
def approve_application(app_id: str, data: ApproveReq):
    ok, msg = eco.process_approval(app_id, data.approver_id, data.approved_amount, data.notes)
    if not ok:
        raise HTTPException(400, msg)
    persistence.save(eco)
    a = eco._all_applications.get(app_id)
    return {"success": True, "message": msg, "application": _app(a) if a else None}


@app.post("/api/applications/{app_id}/reject")
def reject_application(app_id: str, data: RejectReq):
    a = eco._all_applications.get(app_id)
    if not a:
        raise HTTPException(404, "الطلب غير موجود")
    eco.governance.reject_application(a, data.rejector_id, data.reason)
    persistence.save(eco)
    return {"success": True, "application": _app(a)}


@app.post("/api/applications/{app_id}/cancel")
def cancel_application(app_id: str, data: CancelReq):
    a = eco._all_applications.get(app_id)
    if not a:
        raise HTTPException(404, "الطلب غير موجود")
    if not eco.governance.cancel_application(a, data.canceller_id, data.reason):
        raise HTTPException(400, "لا يمكن إلغاء الطلب بحالته الحالية")
    persistence.save(eco)
    return {"success": True, "application": _app(a)}


@app.post("/api/applications/{app_id}/disburse")
def disburse_application(app_id: str, data: DisburseReq = DisburseReq()):
    ok, msg = eco.process_disbursement(app_id, data.executor_id)
    if not ok:
        raise HTTPException(400, msg)
    persistence.save(eco)
    a = eco._all_applications.get(app_id)
    return {"success": True, "message": msg, "application": _app(a) if a else None}


# ── Finance ───────────────────────────────────────────────────────────────────

@app.get("/api/finance/report")
def finance_report():
    return eco.finance.get_financial_report()


@app.get("/api/finance/transactions")
def get_transactions(
    fund_type: str = "",
    limit: int = 30,
    from_date: str = "",
    to_date: str = "",
):
    ft = FundType(fund_type) if fund_type else None
    fd = date.fromisoformat(from_date) if from_date else None
    td = date.fromisoformat(to_date)   if to_date   else None
    txns = eco.finance.get_transactions(ft, limit, fd, td)
    return [_txn(t) for t in reversed(txns)]


@app.post("/api/finance/donate")
def donate(data: DonateReq):
    try:
        ft = FundType(data.fund_type)
    except ValueError:
        raise HTTPException(400, "نوع صندوق غير صحيح")
    ok, msg = eco.finance.receive_donation(
        data.donor_name, data.donor_phone, data.amount, ft, "API"
    )
    if not ok:
        raise HTTPException(400, msg)
    persistence.save(eco)
    return {"success": True, "message": msg, "new_balance": eco.finance.get_balance(ft)}


# ── Sectors ───────────────────────────────────────────────────────────────────

@app.get("/api/sectors")
def get_sectors():
    result = []
    for stype, sector in eco.sectors.items():
        kpi = sector.generate_kpi_report()
        result.append({
            "name":                  stype.value,
            "key":                   stype.name,
            "total_applications":    kpi.total_applications,
            "approved_applications": kpi.approved_applications,
            "rejected_applications": kpi.rejected_applications,
            "total_disbursed":       kpi.total_disbursed,
            "approval_rate":         kpi.approval_rate,
            "beneficiaries_served":  kpi.beneficiaries_served,
            "extra":                 sector.get_sector_specific_info(),
        })
    return result


# ── Audit Log ─────────────────────────────────────────────────────────────────

@app.get("/api/audit-log")
def audit_log(limit: int = 50):
    return eco.governance.get_audit_log(limit)


# ── Alerts ────────────────────────────────────────────────────────────────────

@app.get("/api/alerts")
def get_alerts():
    from utils.alerts import AlertsSystem
    alert_sys = AlertsSystem(eco)
    items = alert_sys.generate()
    alerts = [
        {
            "level":    a.level.upper(),
            "category": a.title,
            "message":  a.message,
            "ref_id":   a.ref_id,
            "date":     str(a.date),
        }
        for a in items
    ]
    return {
        "alerts":         alerts,
        "critical_count": sum(1 for x in alerts if x["level"] == "CRITICAL"),
        "warning_count":  sum(1 for x in alerts if x["level"] == "WARNING"),
        "info_count":     sum(1 for x in alerts if x["level"] == "INFO"),
    }


# ── Zakat Calculator ──────────────────────────────────────────────────────────

@app.get("/api/zakat/nisab")
def zakat_nisab():
    """معلومات النصاب والأسعار المرجعية للزكاة."""
    return {
        "nisab_gold_grams":   85,
        "nisab_silver_grams": 595,
        "zakat_rate":         0.025,
        "gold_price_per_gram_sar":   230.0,
        "silver_price_per_gram_sar": 3.0,
        "nisab_sar":          SmartAI.NISAB_THRESHOLD,
        "categories":         [c.value for c in ZakatCategory],
    }


@app.post("/api/zakat/calculate")
def zakat_calculate(data: ZakatReq):
    NISAB = SmartAI.NISAB_THRESHOLD
    RATE  = 0.025
    G, S, W = 230.0, 3.0, 1.5

    gold_v  = data.gold_grams   * G
    silv_v  = data.silver_grams * S
    crop_v  = data.crops_kg     * W
    cr      = 0.05 if data.irrigated else 0.10

    def chk(label, value, rate, nisab):
        z = value * rate if value >= nisab else 0.0
        return {"label": label, "value": value, "nisab": nisab,
                "rate": rate, "zakat": z, "eligible": value >= nisab}

    results = [
        chk("النقود والأرصدة", data.cash,        RATE, NISAB),
        chk("عروض التجارة",   data.trade_goods,  RATE, NISAB),
        chk("الذهب",          gold_v,            RATE, 85 * G),
        chk("الفضة",          silv_v,            RATE, 595 * S),
        chk("الزراعة",        crop_v,            cr,   653 * W),
        {"label": "الإبل", "value": data.camels,
         "nisab": 5,  "rate": 0, "eligible": data.camels >= 5,
         "zakat": (data.camels // 5) * (0.025 * NISAB) if data.camels >= 5 else 0.0},
        {"label": "البقر", "value": data.cattle,
         "nisab": 30, "rate": 0, "eligible": data.cattle >= 30,
         "zakat": (data.cattle // 30) * (0.025 * NISAB) if data.cattle >= 30 else 0.0},
        {"label": "الغنم", "value": data.sheep,
         "nisab": 40, "rate": 0, "eligible": data.sheep >= 40,
         "zakat": (data.sheep // 40) * (0.025 * NISAB) if data.sheep >= 40 else 0.0},
    ]
    return {
        "results":     results,
        "total_zakat": sum(r["zakat"] for r in results),
        "nisab":       NISAB,
        "categories":  [c.value for c in ZakatCategory],
    }


# ── Hijri ─────────────────────────────────────────────────────────────────────

@app.get("/api/hijri/today")
def hijri_today():
    today = date.today()
    return {
        "gregorian": today.strftime("%Y/%m/%d"),
        "hijri":     HijriCalendar.format_hijri(today.year, today.month, today.day),
        "dual":      HijriCalendar.today_dual(),
    }


# ── System ────────────────────────────────────────────────────────────────────

@app.get("/api/enums")
def get_enums():
    return {
        "fund_types":   [f.value for f in FundType],
        "sector_types": [s.value for s in SectorType],
        "app_statuses": [s.value for s in ApplicationStatus],
        "user_roles":   [r.value for r in UserRole],
        "priorities":   [p.name for p in Priority],
    }


@app.get("/api/users")
def get_users():
    result = []
    for u in eco.governance._users.values():
        result.append({
            "user_id":    u["user_id"],
            "name":       u["name"],
            "role":       u["role"].value if hasattr(u["role"], "value") else str(u["role"]),
            "department": u["department"],
            "created_at": u["created_at"],
            "is_active":  u["is_active"],
        })
    return result


@app.get("/api/policies")
def get_policies():
    return eco.governance.get_policies()


@app.get("/api/config/rules")
def get_config_rules():
    """قواعد الزكاة والأهلية والحدود الشرعية من config/rules.json."""
    import json as _json, pathlib as _pl
    _f = _pl.Path(__file__).resolve().parent.parent / "config" / "rules.json"
    if _f.exists():
        return _json.loads(_f.read_text(encoding="utf-8"))
    return {}


@app.get("/api/config/structure")
def get_config_structure():
    """الهيكل التنظيمي ومصفوفة الصلاحيات من config/structure.json."""
    import json as _json, pathlib as _pl
    _f = _pl.Path(__file__).resolve().parent.parent / "config" / "structure.json"
    if _f.exists():
        return _json.loads(_f.read_text(encoding="utf-8"))
    return {}


@app.post("/api/data/save")
def save_data():
    ok, msg = persistence.save(eco)
    if ok:
        _export_data_files()
    return {"success": ok, "message": msg}


def _export_data_files() -> None:
    """تصدير نسخ منفصلة لبيانات المستفيدين والعمليات والتاريخ في data/."""
    import json as _json
    import pathlib as _pl
    _data = _pl.Path(__file__).resolve().parent.parent / "data"
    _data.mkdir(exist_ok=True)
    _today = str(date.today())

    bens = [
        {"id": b.beneficiary_id, "name": b.full_name, "national_id": b.national_id,
         "city": b.address.city, "family_size": b.family_size,
         "monthly_income": b.monthly_income, "is_eligible": b.is_eligible,
         "is_archived": b.is_archived}
        for b in eco._beneficiaries.values()
    ]
    with open(_data / "beneficiaries.json", "w", encoding="utf-8") as f:
        _json.dump({"_meta": {"exported": _today, "count": len(bens)},
                    "beneficiaries": bens}, f, ensure_ascii=False, indent=2, default=str)

    txns = [
        {"id": t.transaction_id, "fund_type": t.fund_type.value,
         "amount": t.amount, "type": t.transaction_type,
         "description": t.description, "timestamp": str(t.timestamp)[:19]}
        for t in eco.finance.get_transactions(limit=9_999)
    ]
    with open(_data / "transactions.json", "w", encoding="utf-8") as f:
        _json.dump({"_meta": {"exported": _today, "count": len(txns)},
                    "transactions": txns}, f, ensure_ascii=False, indent=2, default=str)

    history = [
        {"id": a.application_id, "sector": a.sector.value, "status": a.status.value,
         "amount": a.approved_amount or a.requested_amount, "ai_score": round(a.ai_score, 2)}
        for a in eco._all_applications.values()
    ]
    with open(_data / "history.json", "w", encoding="utf-8") as f:
        _json.dump({"_meta": {"exported": _today, "purpose": "AI training data",
                               "count": len(history)},
                    "history": history}, f, ensure_ascii=False, indent=2, default=str)


# ── Donors ────────────────────────────────────────────────────────────────────

@app.get("/api/finance/donors")
def get_donors(search: str = ""):
    donors = list(eco.finance._donors.values())
    if search:
        q = search.lower()
        donors = [d for d in donors if q in d.full_name.lower() or q in d.phone]
    return [
        {
            "donor_id":             d.donor_id,
            "full_name":            d.full_name,
            "phone":                d.phone,
            "fund_type":            d.fund_type.value,
            "total_donated":        d.total_donated,
            "donation_count":       d.donation_count,
            "first_donation_date":  str(d.first_donation_date),
            "first_donation_date_h": HijriCalendar.format_hijri(
                d.first_donation_date.year,
                d.first_donation_date.month,
                d.first_donation_date.day,
            ),
        }
        for d in donors
    ]


# ── AI Predictions ────────────────────────────────────────────────────────────

@app.get("/api/ai/predictions")
def ai_predictions():
    apps = list(eco._all_applications.values())
    raw  = eco.ai.predict_future_needs(apps)
    return {
        "predictions": {
            sector.value: round(amount, 2)
            for sector, amount in raw.items()
        },
        "experience_summary": {
            "total_cases": eco.ai.get_experience_summary().get("total_analyzed", 0),
            "avg_score":   round(eco.ai.get_experience_summary().get("average_score", 0), 1),
        },
        "note": "التنبؤات مبنية على التحليل الإحصائي لطلبات السجل الحالي",
    }


# ── Export ────────────────────────────────────────────────────────────────────

@app.get("/api/export/report")
def export_report():
    """تصدير تقرير شامل HTML جاهز للطباعة كـ PDF."""
    import pathlib as _pl
    from smart_charity_ecosystem import CLI
    from fastapi.responses import HTMLResponse
    html = CLI._build_pdf_html(eco)
    _rdir = _pl.Path(__file__).resolve().parent.parent / "reports" / "financial"
    _rdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (_rdir / f"report_{stamp}.html").write_text(html, encoding="utf-8")
    return HTMLResponse(content=html)


@app.get("/api/export/excel")
def export_excel():
    """تصدير جميع البيانات كملف Excel (.xlsx)."""
    import pathlib as _pl
    from smart_charity_ecosystem import CLI
    from fastapi.responses import Response

    BEN_HDR = ["معرّف المستفيد","الاسم","رقم الهوية","الهاتف","المدينة","حجم الأسرة","الدخل","إعاقة","مؤهل"]
    ben_rows = [
        [b.beneficiary_id, b.full_name, b.national_id, b.phone,
         b.address.city, b.family_size, b.monthly_income,
         "نعم" if b.has_disability else "لا", "نعم" if b.is_eligible else "لا"]
        for b in eco._beneficiaries.values()
    ]
    APP_HDR = ["معرّف الطلب","القطاع","الصندوق","المطلوب","المعتمد","الحالة","نقاط الذكاء","التاريخ"]
    app_rows = [
        [a.application_id, a.sector.value, a.fund_type.value,
         a.requested_amount, a.approved_amount, a.status.value,
         f"{a.ai_score:.1f}", str(a.submission_date)]
        for a in eco._all_applications.values()
    ]
    TXN_HDR = ["معرّف العملية","الصندوق","المبلغ","النوع","الوصف","الرصيد بعد","التوقيت"]
    txn_rows = [
        [t.transaction_id, t.fund_type.value, t.amount,
         t.transaction_type, t.description, f"{t.balance_after:.2f}", str(t.timestamp)[:19]]
        for t in eco.finance.get_transactions(limit=9_999)
    ]
    sheets = [
        ("المستفيدون", BEN_HDR, ben_rows),
        ("الطلبات",    APP_HDR, app_rows),
        ("المعاملات",  TXN_HDR, txn_rows),
    ]
    xlsx_bytes = CLI._build_xlsx(sheets)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _pdir = _pl.Path(__file__).resolve().parent.parent / "reports" / "performance"
    _pdir.mkdir(parents=True, exist_ok=True)
    (_pdir / f"data_{stamp}.xlsx").write_bytes(xlsx_bytes)
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="charity_report_{stamp}.xlsx"'},
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  SaaS API v1 — Multi-Tenant Routers  (JWT-authenticated, tenant-isolated)
# ═══════════════════════════════════════════════════════════════════════════════
try:
    from api.v1 import auth as _auth_router
    from api.v1 import beneficiaries as _ben_router
    from api.v1 import applications as _app_router
    from api.v1 import donations as _don_router

    app.include_router(_auth_router.router,  prefix="/api/v1")
    app.include_router(_ben_router.router,   prefix="/api/v1")
    app.include_router(_app_router.router,   prefix="/api/v1")
    app.include_router(_don_router.router,   prefix="/api/v1")
except Exception as _saas_err:  # noqa: BLE001
    import logging as _log
    _log.getLogger(__name__).warning(
        "SaaS routers لم تُحمَّل (python-jose مثبت؟): %s", _saas_err
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
