#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           منظومة العمل الخيري الذكي - Smart Charity Ecosystem              ║
║                   النسخة: 1.0.0  |  تاريخ الإصدار: 2026                    ║
║          نظام متكامل لإدارة الزكاة والصدقات والأوقاف بذكاء اصطناعي        ║
╚══════════════════════════════════════════════════════════════════════════════╝

الوصف:
    منظومة شاملة لإدارة العمل الخيري تضمّ:
      - نواة ذكاء اصطناعي (SmartAI) للتحليل والتقييم الشرعي.
      - نظام حوكمة (GovernanceSystem) متعدد مستويات الصلاحيات.
      - نظام مالي (FinanceSystem) بفصل كامل بين الحسابات.
      - أربعة قطاعات تشغيلية: الصحة، الإسكان، التدوير، الإطعام.

المعايير المتبعة: PEP8 | Google Python Style Guide
"""
from __future__ import annotations

import csv
import hashlib
import io
import zipfile
import json
import logging
import os
import re
import sys
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# إصلاح ترميز المخرجات لدعم العربية والرموز في جميع البيئات
os.environ.setdefault("PYTHONUTF8", "1")
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════════
#  القسم الأول: الألوان والطباعة المنسّقة
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    """ثوابت ألوان ANSI للواجهة النصية."""

    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"


class Printer:
    """أدوات الطباعة المنسّقة للواجهة النصية."""

    WIDTH = 76

    @staticmethod
    def header(title: str) -> None:
        """طباعة رأس القسم الرئيسي."""
        line = "═" * Printer.WIDTH
        print(f"\n{Colors.CYAN}{Colors.BOLD}{line}")
        print(f"  {title}")
        print(f"{line}{Colors.RESET}")

    @staticmethod
    def section(title: str) -> None:
        """طباعة عنوان القسم الفرعي."""
        pad = "─" * (Printer.WIDTH - len(title) - 4)
        print(f"\n{Colors.BLUE}{Colors.BOLD}┌─ {title} {pad}┐{Colors.RESET}")

    @staticmethod
    def success(msg: str) -> None:
        """طباعة رسالة نجاح."""
        print(f"{Colors.GREEN}{Colors.BOLD}  ✓ {msg}{Colors.RESET}")

    @staticmethod
    def error(msg: str) -> None:
        """طباعة رسالة خطأ."""
        print(f"{Colors.RED}{Colors.BOLD}  ✗ {msg}{Colors.RESET}")

    @staticmethod
    def warning(msg: str) -> None:
        """طباعة رسالة تحذير."""
        print(f"{Colors.YELLOW}{Colors.BOLD}  ⚠ {msg}{Colors.RESET}")

    @staticmethod
    def info(msg: str) -> None:
        """طباعة رسالة معلومات."""
        print(f"{Colors.WHITE}  ℹ {msg}{Colors.RESET}")

    @staticmethod
    def kv(key: str, value: Any) -> None:
        """طباعة زوج مفتاح-قيمة بتنسيق جدولي."""
        print(f"  {Colors.CYAN}{key:<32}{Colors.RESET}{Colors.WHITE}{value}{Colors.RESET}")

    @staticmethod
    def divider() -> None:
        """طباعة خط فاصل خفيف."""
        print(f"  {Colors.DIM}{'─' * (Printer.WIDTH - 4)}{Colors.RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
#  التقويم الهجري  (Tabular Islamic Calendar — مكتبة قياسية فقط)
# ═══════════════════════════════════════════════════════════════════════════════

class HijriCalendar:
    """
    تحويل التواريخ الميلادية إلى هجرية وعرضها مزدوجاً.

    الخوارزمية: التقويم الهجري الحسابي الجدولي (Tabular Islamic Calendar).
    المرجعية: يوم اليوليان 1948440 = 1 محرم 1هـ (19 يوليو 622م ميلادي).
    الدقة: مطابقة ±1 يوم لأم القرى في الغالب.
    """

    MONTHS_AR: List[str] = [
        "محرم", "صفر", "ربيع الأول", "ربيع الثاني",
        "جمادى الأولى", "جمادى الآخرة", "رجب", "شعبان",
        "رمضان", "شوال", "ذو القعدة", "ذو الحجة",
    ]

    @staticmethod
    def _g_to_jd(y: int, m: int, d: int) -> int:
        """تحويل ميلادي → رقم يوم يولياني (صحيح، عند الظهر)."""
        if m <= 2:
            y -= 1
            m += 12
        A = y // 100
        B = 2 - A + A // 4
        return (int(365.25 * (y + 4716))
                + int(30.6001 * (m + 1))
                + d + B - 1524)

    @classmethod
    def to_hijri(
        cls, g_year: int, g_month: int, g_day: int
    ) -> Tuple[int, int, int]:
        """
        تحويل تاريخ ميلادي إلى هجري.

        المدخلات:
            g_year, g_month, g_day: أجزاء التاريخ الميلادي.

        المخرجات:
            (h_year, h_month, h_day) — السنة والشهر واليوم الهجري.
        """
        jd = cls._g_to_jd(g_year, g_month, g_day)
        n  = jd - 1948440

        hy  = (30 * n + 10661) // 10631
        jd0 = (10631 * hy - 10617) // 30 + 1948440

        doy = jd - jd0 + 1
        hm, hd = 1, doy
        for m in range(1, 13):
            dm = 30 if m % 2 == 1 else 29
            if m == 12 and (11 * hy + 14) % 30 < 11:
                dm = 30
            if hd <= dm:
                hm = m
                break
            hd -= dm

        return hy, hm, hd

    @classmethod
    def format_hijri(cls, g_year: int, g_month: int, g_day: int) -> str:
        """إرجاع التاريخ الهجري بالعربية — مثال: '19 جمادى الآخرة 1445هـ'."""
        hy, hm, hd = cls.to_hijri(g_year, g_month, g_day)
        return f"{hd} {cls.MONTHS_AR[hm - 1]} {hy}هـ"

    @classmethod
    def dual(cls, d: "date") -> str:
        """
        تاريخ مزدوج ميلادي-هجري على سطر واحد.

        مثال: '2024/01/19م  |  19 جمادى الآخرة 1445هـ'
        """
        return f"{d.strftime('%Y/%m/%d')}م  |  {cls.format_hijri(d.year, d.month, d.day)}"

    @classmethod
    def today_dual(cls) -> str:
        """اليوم الحالي بالتقويمين."""
        return cls.dual(date.today())


# ═══════════════════════════════════════════════════════════════════════════════
#  القسم الثاني: التعدادات
# ═══════════════════════════════════════════════════════════════════════════════

class ZakatCategory(Enum):
    """مصارف الزكاة الثمانية (التوبة: 60)."""

    FUQARA    = "الفقراء"
    MASAKIN   = "المساكين"
    AMILIN    = "العاملون عليها"
    MUALLAFA  = "المؤلفة قلوبهم"
    RIQAB     = "في الرقاب"
    GHARIMIN  = "الغارمون"
    FI_SABIL  = "في سبيل الله"
    IBN_SABIL = "ابن السبيل"


class FundType(Enum):
    """أنواع الصناديق المالية — يُمنع الخلط بينها شرعاً وإدارياً."""

    ZAKAT      = "الزكاة"
    SADAQAT    = "الصدقات"
    AWQAF      = "الأوقاف"
    RESTRICTED = "المشاريع المقيدة"


class ApplicationStatus(Enum):
    """حالات دورة حياة الطلب."""

    DRAFT            = "مسودة"
    SUBMITTED        = "مقدَّم"
    AI_ANALYZED      = "تم التحليل الذكي"
    PENDING_APPROVAL = "بانتظار الموافقة"
    APPROVED         = "موافق عليه"
    REJECTED         = "مرفوض"
    DISBURSED        = "تم الصرف"
    CANCELLED        = "ملغى"
    CLOSED           = "مغلق"


class Priority(Enum):
    """مستويات الأولوية لترتيب المعالجة."""

    CRITICAL = 1
    HIGH     = 2
    MEDIUM   = 3
    LOW      = 4


class UserRole(Enum):
    """أدوار المستخدمين وصلاحياتهم."""

    SYSTEM_ADMIN  = "مدير النظام"
    EXECUTIVE_DIR = "المدير التنفيذي"
    FINANCE_MGR   = "مدير المالية"
    SECTOR_MGR    = "مدير القطاع"
    CASE_WORKER   = "أخصائي حالات"
    AUDITOR       = "مدقق"
    DATA_ENTRY    = "مدخل بيانات"


class SectorType(Enum):
    """أنواع القطاعات التشغيلية الأربعة."""

    HEALTH    = "الصحة"
    HOUSING   = "الإسكان"
    RECYCLING = "التدوير والاستدامة"
    FOOD      = "الإطعام وحفظ النعمة"


# ═══════════════════════════════════════════════════════════════════════════════
#  القسم الثالث: نماذج البيانات
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Address:
    """نموذج العنوان الجغرافي."""

    city: str
    district: str
    street: str = ""

    def __str__(self) -> str:
        return f"{self.city} - {self.district}"


@dataclass
class Beneficiary:
    """
    نموذج بيانات المستفيد.

    الحقول:
        full_name: الاسم الكامل.
        national_id: رقم الهوية الوطنية.
        phone: رقم الجوال.
        address: العنوان.
        family_size: عدد أفراد الأسرة.
        monthly_income: الدخل الشهري (ريال).
        is_employed: موظف بدخل مستقر؟
        has_disability: يعاني من إعاقة؟
        zakat_category: مصرف الزكاة المنطبق (تُحدده SmartAI).
        is_eligible: حالة الأهلية (تُحدده SmartAI).
        eligibility_notes: ملاحظات الأهلية.
    """

    full_name: str
    national_id: str
    phone: str
    address: Address
    family_size: int
    monthly_income: float
    is_employed: bool = False
    has_disability: bool = False
    zakat_category: Optional[ZakatCategory] = None
    beneficiary_id: str = field(
        default_factory=lambda: "BEN-" + str(uuid.uuid4())[:8].upper()
    )
    registration_date: date = field(default_factory=date.today)
    is_eligible: Optional[bool] = None
    eligibility_notes: str = ""
    is_archived: bool = False
    tenant_id:   str  = "default"

    def get_income_per_capita(self) -> float:
        """حساب نصيب الفرد من الدخل الشهري."""
        return self.monthly_income / max(self.family_size, 1)


@dataclass
class Application:
    """
    نموذج طلب المساعدة.

    الحقول:
        beneficiary_id: معرّف مقدّم الطلب.
        sector: القطاع التشغيلي المعني.
        requested_amount: المبلغ المطلوب (ريال).
        fund_type: الصندوق المالي المراد الصرف منه.
        description: وصف تفصيلي للحاجة.
        supporting_docs: المستندات الداعمة.
        ai_score: نقاط تقييم الذكاء الاصطناعي (0–100).
        ai_recommendation: توصية الذكاء الاصطناعي.
        approved_amount: المبلغ المعتمد فعلياً.
        audit_trail: سجل الإجراءات المتسلسل.
    """

    beneficiary_id: str
    sector: SectorType
    requested_amount: float
    fund_type: FundType
    description: str
    supporting_docs: List[str] = field(default_factory=list)
    application_id: str = field(
        default_factory=lambda: "APP-" + str(uuid.uuid4())[:8].upper()
    )
    status: ApplicationStatus = ApplicationStatus.DRAFT
    priority: Priority = Priority.MEDIUM
    ai_score: float = 0.0
    ai_recommendation: str = ""
    approved_amount: float = 0.0
    approver_id: Optional[str] = None
    submission_date: date = field(default_factory=date.today)
    approval_date: Optional[date] = None
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    tenant_id:   str                  = "default"

    def add_audit_entry(self, action: str, actor: str, notes: str = "") -> None:
        """إضافة إدخال لسجل التدقيق الخاص بالطلب."""
        self.audit_trail.append({
            "timestamp": datetime.now().isoformat(),
            "action":    action,
            "actor":     actor,
            "notes":     notes,
        })


@dataclass
class Transaction:
    """
    نموذج العملية المالية.

    الحقول:
        fund_type: الصندوق المعني.
        amount: قيمة العملية (ريال).
        transaction_type: "CREDIT" إيداع أو "DEBIT" سحب.
        reference_id: مرجع العملية (طلب/متبرع).
        description: وصف العملية.
        executor_id: منفّذ العملية.
        balance_after: الرصيد بعد العملية.
        checksum: بصمة SHA-256 للتحقق من السلامة.
    """

    fund_type: FundType
    amount: float
    transaction_type: str
    reference_id: str
    description: str
    executor_id: str
    balance_after: float
    transaction_id: str = field(
        default_factory=lambda: "TXN-" + str(uuid.uuid4())[:10].upper()
    )
    timestamp:      datetime      = field(default_factory=datetime.now)
    tenant_id:      str           = "default"
    application_id: Optional[str] = None
    checksum:       str           = field(init=False)

    def __post_init__(self) -> None:
        """حساب البصمة الأمنية بعد التهيئة."""
        raw = f"{self.transaction_id}{self.amount}{self.fund_type.value}{self.timestamp}"
        self.checksum = hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class DonorRecord:
    """نموذج بيانات المتبرع."""

    full_name: str
    phone: str
    fund_type: FundType
    total_donated: float = 0.0
    donor_id: str = field(
        default_factory=lambda: "DNR-" + str(uuid.uuid4())[:8].upper()
    )
    first_donation_date: date = field(default_factory=date.today)
    donation_count: int = 0
    tenant_id:      str = "default"

    def record_donation(self, amount: float) -> None:
        """تحديث إجمالي تبرعات المتبرع."""
        self.total_donated += amount
        self.donation_count += 1


@dataclass
class KPIReport:
    """تقرير مؤشرات الأداء الرئيسية لقطاع."""

    sector: SectorType
    report_date: date
    total_applications: int
    approved_applications: int
    rejected_applications: int
    total_disbursed: float
    beneficiaries_served: int

    @property
    def approval_rate(self) -> float:
        """نسبة الموافقة المئوية."""
        if self.total_applications == 0:
            return 0.0
        return (self.approved_applications / self.total_applications) * 100


# ═══════════════════════════════════════════════════════════════════════════════
#  القسم الرابع: نواة الذكاء الاصطناعي
# ═══════════════════════════════════════════════════════════════════════════════

class SmartAI:
    """
    نواة الذكاء الاصطناعي لمنظومة العمل الخيري.

    المهام:
        - التحقق من أهلية المستفيدين وفق الضوابط الشرعية.
        - تحليل الطلبات وتقييمها وتحديد أولوياتها.
        - اقتراح المبالغ الملائمة للصرف.
        - التنبؤ بالاحتياجات المستقبلية.
        - التعلم من الحالات السابقة عبر قاعدة الخبرات.
    """

    NISAB_THRESHOLD: float = 5_000.0
    MAX_ELIGIBLE_INCOME_PER_CAPITA: float = 2_500.0
    MAX_ZAKAT_PER_APPLICATION: float = 15_000.0

    def __init__(self) -> None:
        """تهيئة الذكاء الاصطناعي وقاعدة بيانات الخبرات."""
        self._logger = logging.getLogger(self.__class__.__name__)
        self._experience_db: List[Dict[str, Any]] = []

    def check_eligibility(self, beneficiary: Beneficiary) -> Tuple[bool, str]:
        """
        التحقق من أهلية المستفيد وفق القاعدة الشرعية:
        «لا يُصرف لغني ولا لقوي مكتسب».

        المدخلات:
            beneficiary: نموذج بيانات المستفيد.

        المخرجات:
            (is_eligible, reason): الأهلية وسببها.
        """
        income_pc = beneficiary.get_income_per_capita()

        if (
            beneficiary.monthly_income >= self.NISAB_THRESHOLD
            and not beneficiary.has_disability
        ):
            return False, "الدخل يتجاوز حد النصاب — غير مستحق للزكاة"

        if (
            beneficiary.is_employed
            and income_pc >= self.MAX_ELIGIBLE_INCOME_PER_CAPITA
            and not beneficiary.has_disability
        ):
            return False, "موظف بدخل كافٍ — لا يُصرف للقوي المكتسب"

        category = self._determine_zakat_category(beneficiary)
        if category:
            beneficiary.zakat_category = category
            return True, f"مؤهل — الفئة: {category.value}"

        return True, "مؤهل للمساعدة من الصدقات"

    def _determine_zakat_category(
        self, beneficiary: Beneficiary
    ) -> Optional[ZakatCategory]:
        """
        تحديد مصرف الزكاة المناسب.

        المدخلات:
            beneficiary: نموذج بيانات المستفيد.

        المخرجات:
            فئة الزكاة أو None.
        """
        income_pc = beneficiary.get_income_per_capita()
        if income_pc < 500:
            return ZakatCategory.FUQARA
        if income_pc < self.MAX_ELIGIBLE_INCOME_PER_CAPITA:
            return ZakatCategory.MASAKIN
        if beneficiary.has_disability:
            return ZakatCategory.MASAKIN
        return None

    def analyze_application(
        self,
        application: Application,
        beneficiary: Beneficiary,
    ) -> Tuple[float, Priority, str]:
        """
        تحليل طلب مساعدة وتقييمه.

        المدخلات:
            application: نموذج الطلب.
            beneficiary: نموذج المستفيد.

        المخرجات:
            (score, priority, recommendation): النقاط والأولوية والتوصية.
        """
        score = 50.0

        income_ratio = (
            beneficiary.get_income_per_capita() / self.MAX_ELIGIBLE_INCOME_PER_CAPITA
        )
        score += (1 - min(income_ratio, 1.0)) * 25
        score += min(beneficiary.family_size * 2, 15)

        if beneficiary.has_disability:
            score += 10
        if application.sector == SectorType.HEALTH:
            score += 15
        if application.supporting_docs:
            score += 5

        score = min(score, 100.0)
        priority = self._score_to_priority(score, application.sector)
        suggested = self._suggest_amount(
            application.requested_amount, beneficiary, application.sector
        )
        recommendation = (
            f"النقاط: {score:.1f}/100 | الأولوية: {priority.name} | "
            f"المبلغ المقترح: {suggested:,.2f} ريال"
        )
        self._log_experience(application, beneficiary, score, priority)
        return score, priority, recommendation

    def _score_to_priority(self, score: float, sector: SectorType) -> Priority:
        """تحويل النقاط إلى مستوى أولوية."""
        if score >= 85 or sector == SectorType.HEALTH:
            return Priority.CRITICAL
        if score >= 70:
            return Priority.HIGH
        if score >= 50:
            return Priority.MEDIUM
        return Priority.LOW

    def _suggest_amount(
        self,
        requested: float,
        beneficiary: Beneficiary,
        sector: SectorType,
    ) -> float:
        """
        اقتراح مبلغ ملائم ضمن الضوابط الشرعية.

        المدخلات:
            requested: المبلغ المطلوب.
            beneficiary: بيانات المستفيد.
            sector: القطاع المعني.

        المخرجات:
            المبلغ المقترح للصرف.
        """
        base = beneficiary.family_size * 500
        multipliers: Dict[SectorType, float] = {
            SectorType.HEALTH:    3.0,
            SectorType.HOUSING:   2.5,
            SectorType.FOOD:      1.0,
            SectorType.RECYCLING: 1.5,
        }
        ceiling = min(base * multipliers.get(sector, 1.5), self.MAX_ZAKAT_PER_APPLICATION)
        return min(requested, ceiling)

    def predict_future_needs(
        self, applications: List[Application]
    ) -> Dict[SectorType, float]:
        """
        التنبؤ بالاحتياجات المالية للشهر القادم (معامل نمو 10%).

        المدخلات:
            applications: الطلبات التاريخية.

        المخرجات:
            قاموس {قطاع: المبلغ المتوقع}.
        """
        totals: Dict[SectorType, float] = {s: 0.0 for s in SectorType}
        counts: Dict[SectorType, int]   = {s: 0   for s in SectorType}
        for app in applications:
            if app.status == ApplicationStatus.APPROVED:
                totals[app.sector] += app.approved_amount
                counts[app.sector] += 1
        return {
            s: (totals[s] / max(counts[s], 1)) * 1.10
            for s in SectorType
        }

    def generate_holistic_plan(
        self,
        field_notes: str,
        beneficiary: "Beneficiary",
    ) -> "List[Application]":
        """
        توليد خطة تدخل شاملة من الملاحظات الميدانية.

        يحلل النص المدخل ويستخرج الاحتياجات المتعددة للمستفيد، فيُنشئ
        طلبات مساعدة في القطاعات المناسبة بدلاً من طلب واحد، خدمةً
        للمستفيد كإنسان متكامل الاحتياجات.

        المدخلات:
            field_notes: الملاحظات الميدانية (نص حر).
            beneficiary: كائن بيانات المستفيد.

        المخرجات:
            قائمة من كائنات Application جاهزة للتقديم عبر submit_application.
        """
        SECTOR_KEYWORDS: Dict[SectorType, List[str]] = {
            SectorType.HEALTH: [
                "صحة", "طبي", "مرض", "علاج", "دواء", "مستشفى",
                "إعاقة", "عملية", "أشعة", "كلى", "قلب", "سرطان",
            ],
            SectorType.HOUSING: [
                "سكن", "إيجار", "مسكن", "منزل", "بيت",
                "إسكان", "إيواء", "شقة", "مأوى",
            ],
            SectorType.FOOD: [
                "غذاء", "طعام", "مؤونة", "جوع", "مواد غذائية",
                "سلة غذائية", "إطعام", "وجبة",
            ],
            SectorType.RECYCLING: [
                "أثاث", "ملابس", "تدوير", "أجهزة", "مستلزمات",
                "ثلاجة", "غسالة", "مفروشات",
            ],
        }
        SECTOR_FUND: Dict[SectorType, FundType] = {
            SectorType.HEALTH:    FundType.SADAQAT,
            SectorType.HOUSING:   FundType.AWQAF,
            SectorType.FOOD:      FundType.ZAKAT,
            SectorType.RECYCLING: FundType.SADAQAT,
        }
        SECTOR_AMOUNT: Dict[SectorType, float] = {
            SectorType.HEALTH:    3_000.0,
            SectorType.HOUSING:   5_000.0,
            SectorType.FOOD:      1_500.0,
            SectorType.RECYCLING: 800.0,
        }

        plans: List[Application] = []
        excerpt = field_notes[:200]

        for sector, keywords in SECTOR_KEYWORDS.items():
            if any(kw in field_notes for kw in keywords):
                app = Application(
                    beneficiary_id=beneficiary.beneficiary_id,
                    sector=sector,
                    requested_amount=SECTOR_AMOUNT[sector],
                    fund_type=SECTOR_FUND[sector],
                    description=f"[خطة شاملة — {sector.value}] {excerpt}",
                    tenant_id=beneficiary.tenant_id,
                )
                _, app.priority, app.ai_recommendation = self.analyze_application(
                    app, beneficiary
                )
                plans.append(app)

        if not plans:
            app = Application(
                beneficiary_id=beneficiary.beneficiary_id,
                sector=SectorType.FOOD,
                requested_amount=2_000.0,
                fund_type=FundType.ZAKAT,
                description=f"[خطة شاملة — عامة] {excerpt}",
                tenant_id=beneficiary.tenant_id,
            )
            plans.append(app)

        self._logger.info(
            "خطة شاملة: %d طلبات للمستفيد %s",
            len(plans), beneficiary.beneficiary_id,
        )
        return plans

    def _log_experience(
        self,
        application: Application,
        beneficiary: Beneficiary,
        score: float,
        priority: Priority,
    ) -> None:
        """تسجيل الحالة في قاعدة الخبرات للتعلم المستقبلي."""
        self._experience_db.append({
            "application_id":  application.application_id,
            "sector":          application.sector.value,
            "score":           score,
            "priority":        priority.name,
            "income_per_capita": beneficiary.get_income_per_capita(),
            "family_size":     beneficiary.family_size,
            "has_disability":  beneficiary.has_disability,
            "timestamp":       datetime.now().isoformat(),
        })

    def get_experience_summary(self) -> Dict[str, Any]:
        """
        ملخص إحصائي لقاعدة الخبرات.

        المخرجات:
            قاموس إحصائي بالحالات المحللة.
        """
        if not self._experience_db:
            return {"total_analyzed": 0}
        scores = [e["score"] for e in self._experience_db]
        high   = sum(
            1 for e in self._experience_db
            if e["priority"] in ("CRITICAL", "HIGH")
        )
        return {
            "total_analyzed":      len(self._experience_db),
            "average_score":       sum(scores) / len(scores),
            "high_priority_count": high,
        }

    # ── واجهات متوافقة مع المواصفات (Spec-compatible API) ─────────────────────

    def learn_from_history(self, historical_data: List[Dict[str, Any]]) -> None:
        """
        تغذية قاعدة الخبرات بالبيانات التاريخية للتعلم التراكمي.

        المدخلات:
            historical_data: قائمة بالحالات والعمليات السابقة.
        """
        if not historical_data:
            return
        for entry in historical_data:
            self._experience_db.append({
                "application_id":    entry.get("id", ""),
                "sector":            entry.get("sector", ""),
                "score":             float(entry.get("ai_score", 50)),
                "priority":          entry.get("priority", "MEDIUM"),
                "income_per_capita": entry.get("income_per_capita", 0),
                "family_size":       entry.get("family_size", 1),
                "has_disability":    entry.get("has_disability", False),
                "timestamp":         entry.get("date", datetime.now().isoformat()),
            })
        self._logger.info(
            "تم تحميل %d سجل تاريخي في قاعدة الخبرات", len(historical_data)
        )

    def evaluate_eligibility(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        تقييم استحقاق الحالة — واجهة موحّدة تُرجع قاموساً مفصّلاً.

        المدخلات:
            case_data: بيانات الحالة (income, family_size, has_disability, fund_type).

        المخرجات:
            قاموس: is_eligible, reason, recommendations, confidence_level.
        """
        tmp = Beneficiary(
            full_name="تقييم_مؤقت",
            national_id="0000000000",
            phone="0500000000",
            address=Address(city="", district=""),
            family_size=max(int(case_data.get("family_size", 1)), 1),
            monthly_income=float(case_data.get("beneficiary_income", 0)),
            has_disability=bool(case_data.get("has_disability", False)),
            registration_date=date.today(),
        )
        is_elig, reason = self.check_eligibility(tmp)
        summary = self.get_experience_summary()
        recs: List[Dict[str, Any]] = []
        if summary.get("total_analyzed", 0) > 0:
            recs.append({
                "suggested_amount": round(self.MAX_ZAKAT_PER_APPLICATION * 0.3, 2),
                "based_on": f"{summary['total_analyzed']} حالة سابقة في قاعدة الخبرات",
            })
        confidence = round(min(0.95, 0.70 + len(self._experience_db) * 0.005), 2)
        return {
            "is_eligible":      is_elig,
            "reason":           reason,
            "recommendations":  recs,
            "confidence_level": confidence,
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  القسم الخامس: نظام الحوكمة وإدارة الصلاحيات
# ═══════════════════════════════════════════════════════════════════════════════

class GovernanceSystem:
    """
    نظام الحوكمة وإدارة الصلاحيات متعدد المستويات.

    يوفر:
        - مصفوفة صلاحيات الموافقة حسب الدور الوظيفي.
        - تسجيل وأرشفة جميع القرارات والإجراءات.
        - السياسات والإجراءات المعتمدة.
    """

    APPROVAL_MATRIX: Dict[UserRole, float] = {
        UserRole.SYSTEM_ADMIN:  float("inf"),
        UserRole.EXECUTIVE_DIR: float("inf"),
        UserRole.FINANCE_MGR:   50_000.0,
        UserRole.SECTOR_MGR:    15_000.0,
        UserRole.CASE_WORKER:    5_000.0,
        UserRole.AUDITOR:            0.0,
        UserRole.DATA_ENTRY:         0.0,
    }

    def __init__(self) -> None:
        """تهيئة نظام الحوكمة بالسياسات الافتراضية."""
        self._logger   = logging.getLogger(self.__class__.__name__)
        self._users:     Dict[str, Dict[str, Any]] = {}
        self._audit_log: List[Dict[str, Any]]      = []
        self._policies   = self._init_policies()

    def _init_policies(self) -> List[Dict[str, str]]:
        """تهيئة السياسات والإجراءات الافتراضية المعتمدة."""
        return [
            {
                "code": "POL-001",
                "title": "سياسة صرف الزكاة",
                "description": "لا يجوز صرف الزكاة لغني أو لقوي مكتسب وفق الضوابط الشرعية.",
            },
            {
                "code": "POL-002",
                "title": "سياسة الفصل المالي",
                "description": "فصل تام بين حسابات الزكاة والصدقات والأوقاف والمشاريع المقيدة.",
            },
            {
                "code": "POL-003",
                "title": "سياسة التدقيق والشفافية",
                "description": "تسجيل جميع العمليات والقرارات في سجل تدقيق محمي.",
            },
            {
                "code": "POL-004",
                "title": "سياسة الموافقة متعددة المستويات",
                "description": "كل مبلغ يستلزم موافقة الجهة المختصة وفق مصفوفة الصلاحيات.",
            },
        ]

    def register_user(
        self, name: str, role: UserRole, department: str
    ) -> str:
        """
        تسجيل مستخدم جديد في النظام.

        المدخلات:
            name: اسم المستخدم الكامل.
            role: الدور الوظيفي.
            department: القسم أو الإدارة.

        المخرجات:
            معرّف المستخدم الجديد.
        """
        user_id = "USR-" + str(uuid.uuid4())[:8].upper()
        self._users[user_id] = {
            "user_id":    user_id,
            "name":       name,
            "role":       role,
            "department": department,
            "created_at": datetime.now().isoformat(),
            "is_active":  True,
        }
        self._record_audit(
            action="USER_REGISTERED",
            actor="SYSTEM",
            details=f"المستخدم: {name} | الدور: {role.value}",
        )
        return user_id

    def can_approve(self, user_id: str, amount: float) -> bool:
        """
        التحقق من صلاحية الموافقة على مبلغ محدد.

        المدخلات:
            user_id: معرّف المستخدم.
            amount: قيمة المبلغ.

        المخرجات:
            True إذا كان يملك الصلاحية.
        """
        user = self._users.get(user_id)
        if not user or not user["is_active"]:
            return False
        limit = self.APPROVAL_MATRIX.get(user["role"], 0.0)
        return amount <= limit

    def approve_application(
        self,
        application: Application,
        approver_id: str,
        approved_amount: float,
        notes: str = "",
    ) -> bool:
        """
        تنفيذ الموافقة الرسمية على طلب.

        المدخلات:
            application: الطلب المراد الموافقة عليه.
            approver_id: معرّف الموافق.
            approved_amount: المبلغ المعتمد.
            notes: ملاحظات إضافية.

        المخرجات:
            True عند النجاح.
        """
        if not self.can_approve(approver_id, approved_amount):
            self._logger.warning(
                "المستخدم %s لا يملك صلاحية الموافقة على %.2f ريال",
                approver_id, approved_amount,
            )
            return False

        application.status         = ApplicationStatus.APPROVED
        application.approved_amount = approved_amount
        application.approver_id    = approver_id
        application.approval_date  = date.today()
        application.add_audit_entry(
            action="APPROVED",
            actor=approver_id,
            notes=f"المبلغ المعتمد: {approved_amount:,.2f} ريال. {notes}",
        )
        self._record_audit(
            action="APPLICATION_APPROVED",
            actor=approver_id,
            details=(
                f"الطلب: {application.application_id} | "
                f"المبلغ: {approved_amount:,.2f} ريال"
            ),
        )
        return True

    def reject_application(
        self,
        application: Application,
        rejector_id: str,
        reason: str,
    ) -> None:
        """
        رفض طلب مع توثيق السبب.

        المدخلات:
            application: الطلب المراد رفضه.
            rejector_id: معرّف الرافض.
            reason: سبب الرفض.
        """
        application.status = ApplicationStatus.REJECTED
        application.add_audit_entry(
            action="REJECTED", actor=rejector_id, notes=reason
        )
        self._record_audit(
            action="APPLICATION_REJECTED",
            actor=rejector_id,
            details=f"الطلب: {application.application_id} | السبب: {reason}",
        )

    def cancel_application(
        self,
        application: Application,
        canceller_id: str,
        reason: str = "",
    ) -> bool:
        """
        إلغاء طلب مساعدة.

        يُسمح بالإلغاء ما لم يكن الطلب قد صُرف أو أُغلق بالفعل.

        المدخلات:
            application: الطلب المراد إلغاؤه.
            canceller_id: معرّف منفّذ الإلغاء.
            reason: سبب الإلغاء (اختياري).

        المخرجات:
            True  عند نجاح الإلغاء.
            False إذا كانت الحالة لا تسمح بالإلغاء.
        """
        non_cancellable = {
            ApplicationStatus.DISBURSED,
            ApplicationStatus.CANCELLED,
            ApplicationStatus.CLOSED,
        }
        if application.status in non_cancellable:
            return False
        application.status = ApplicationStatus.CANCELLED
        application.add_audit_entry(
            action="CANCELLED", actor=canceller_id, notes=reason
        )
        self._record_audit(
            action="APPLICATION_CANCELLED",
            actor=canceller_id,
            details=(
                f"الطلب: {application.application_id} | "
                f"السبب: {reason or 'غير محدد'}"
            ),
        )
        return True

    def fast_track_approve(
        self,
        application: "Application",
        amount: float,
        notes: str = "مسار الطوارئ السريع — اعتماد تلقائي",
    ) -> None:
        """
        اعتماد تلقائي للحالات الحرجة متجاوزاً مصفوفة الصلاحيات.

        يُستدعى تلقائياً عند اكتشاف طلب بأولوية CRITICAL ومبلغ
        أقل من FAST_TRACK_LIMIT — دون انتظار موافقة إدارية.

        المدخلات:
            application: الطلب الحرج.
            amount: المبلغ المعتمد.
            notes: ملاحظات الاعتماد.
        """
        application.status          = ApplicationStatus.APPROVED
        application.approved_amount = amount
        application.approver_id     = "FAST-TRACK-SYSTEM"
        application.approval_date   = date.today()
        application.add_audit_entry(
            action="FAST_TRACK_APPROVED",
            actor="FAST-TRACK-SYSTEM",
            notes=notes,
        )
        self._record_audit(
            action="FAST_TRACK_APPROVED",
            actor="FAST-TRACK-SYSTEM",
            details=(
                f"طوارئ تلقائي: {application.application_id} | "
                f"المبلغ: {amount:,.2f} ريال | "
                f"الأولوية: {application.priority.name}"
            ),
        )

    def _record_audit(
        self, action: str, actor: str, details: str
    ) -> None:
        """
        تسجيل حدث في سجل التدقيق المركزي.

        المدخلات:
            action: نوع الإجراء.
            actor: منفّذ الإجراء.
            details: تفاصيل الحدث.
        """
        self._audit_log.append({
            "log_id":    "LOG-" + str(uuid.uuid4())[:8].upper(),
            "timestamp": datetime.now().isoformat(),
            "action":    action,
            "actor":     actor,
            "details":   details,
        })

    def get_audit_log(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        استرجاع آخر سجلات التدقيق.

        المدخلات:
            limit: عدد السجلات.

        المخرجات:
            قائمة السجلات.
        """
        return self._audit_log[-limit:]

    def get_policies(self) -> List[Dict[str, str]]:
        """استرجاع السياسات والإجراءات المعتمدة."""
        return self._policies.copy()

    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """استرجاع بيانات مستخدم بمعرّفه."""
        return self._users.get(user_id)

    # ── واجهات متوافقة مع المواصفات (Spec-compatible API) ─────────────────────

    def setup_organization_structure(
        self, structure_data: Dict[str, Any]
    ) -> None:
        """
        بناء وتسجيل الهيكل التنظيمي المعتمد.

        المدخلات:
            structure_data: قاموس بالأقسام والوظائف وأدوارهم.
        """
        for dept, members in structure_data.items():
            if not isinstance(members, dict):
                continue
            for uid, info in members.items():
                role_name = info.get("role", "DATA_ENTRY").upper()
                try:
                    role = UserRole[role_name]
                except KeyError:
                    role = UserRole.DATA_ENTRY
                self.register_user(
                    name=info.get("name", uid),
                    role=role,
                    department=dept,
                )
        self._logger.info("تم اعتماد الهيكل التنظيمي وتوزيع الصلاحيات")

    def get_approval_authority(self, amount: float) -> str:
        """
        تحديد الجهة المخولة بالموافقة بناءً على قيمة المبلغ.

        المدخلات:
            amount: قيمة المبلغ (ريال).

        المخرجات:
            اسم الدور الوظيفي المخوَّل.
        """
        if amount < self.APPROVAL_MATRIX[UserRole.CASE_WORKER]:
            return UserRole.CASE_WORKER.value
        if amount < self.APPROVAL_MATRIX[UserRole.SECTOR_MGR]:
            return UserRole.SECTOR_MGR.value
        if amount < self.APPROVAL_MATRIX[UserRole.FINANCE_MGR]:
            return UserRole.FINANCE_MGR.value
        return UserRole.EXECUTIVE_DIR.value

    def record_decision(self, decision_data: Dict[str, Any]) -> str:
        """
        تسجيل القرار في سجل التدقيق مع تحديد الجهة المعتمِدة.

        المدخلات:
            decision_data: بيانات القرار (amount, application_id, ...).

        المخرجات:
            معرّف القرار المسجَّل.
        """
        amount    = float(decision_data.get("amount", 0))
        authority = self.get_approval_authority(amount)
        decision_id = f"DEC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        app_id = str(decision_data.get("application_id", ""))
        self._record_audit(
            action=decision_data.get("action", "تسجيل قرار"),
            actor=authority,
            details=f"طلب: {app_id} | المبلغ: {amount:,.2f} | القرار: {decision_id}",
        )
        return decision_id


# ═══════════════════════════════════════════════════════════════════════════════
#  القسم السادس: النظام المالي
# ═══════════════════════════════════════════════════════════════════════════════

class FinanceSystem:
    """
    النظام المالي لمنظومة العمل الخيري.

    يضمن:
        - فصلاً تاماً بين الزكاة والصدقات والأوقاف والمشاريع المقيدة.
        - استقبال التبرعات وتسجيل بيانات المتبرعين.
        - صرف الأموال وفق الضوابط الشرعية والإدارية.
        - تقارير مالية دقيقة وشاملة.

    تحذير شرعي: يُحظر تماماً خلط أموال الزكاة بغيرها.
    """

    def __init__(self) -> None:
        """تهيئة النظام المالي بأرصدة صفرية."""
        self._logger       = logging.getLogger(self.__class__.__name__)
        self._balances:    Dict[FundType, float]   = {f: 0.0 for f in FundType}
        self._transactions: List[Transaction]      = []
        self._donors:      Dict[str, DonorRecord]  = {}

    def receive_donation(
        self,
        donor_name: str,
        donor_phone: str,
        amount: float,
        fund_type: FundType,
        executor_id: str,
        application_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        استقبال تبرع وإيداعه في الصندوق الصحيح.

        المدخلات:
            donor_name: اسم المتبرع.
            donor_phone: هاتف المتبرع.
            amount: قيمة التبرع (ريال).
            fund_type: الصندوق المستفيد.
            executor_id: معرّف الموظف المستلم.
            application_id: ربط اختياري بطلب مستفيد محدد (حلقة الأثر).

        المخرجات:
            (success, message).
        """
        if amount <= 0:
            return False, "قيمة التبرع يجب أن تكون أكبر من صفر"

        self._balances[fund_type] += amount
        txn = Transaction(
            fund_type=fund_type,
            amount=amount,
            transaction_type="CREDIT",
            reference_id=donor_phone,
            description=f"تبرع من: {donor_name}",
            executor_id=executor_id,
            balance_after=self._balances[fund_type],
            application_id=application_id,
        )
        self._transactions.append(txn)

        key = f"{donor_phone}_{fund_type.value}"
        if key not in self._donors:
            self._donors[key] = DonorRecord(
                full_name=donor_name,
                phone=donor_phone,
                fund_type=fund_type,
            )
        self._donors[key].record_donation(amount)
        return True, f"تم استلام {amount:,.2f} ريال في حساب {fund_type.value}"

    def disburse_funds(
        self,
        application: Application,
        executor_id: str,
    ) -> Tuple[bool, str]:
        """
        صرف الأموال لطلب معتمد.

        المدخلات:
            application: الطلب المعتمد.
            executor_id: معرّف منفّذ الصرف.

        المخرجات:
            (success, message).
        """
        if application.status != ApplicationStatus.APPROVED:
            return False, "الصرف يقتصر على الطلبات المعتمدة فقط"

        if application.approved_amount <= 0:
            return False, "لم يُحدد مبلغ معتمد"

        fund = application.fund_type
        if self._balances[fund] < application.approved_amount:
            return False, (
                f"رصيد {fund.value} غير كافٍ. "
                f"المتاح: {self._balances[fund]:,.2f} ريال"
            )

        self._balances[fund] -= application.approved_amount
        txn = Transaction(
            fund_type=fund,
            amount=application.approved_amount,
            transaction_type="DEBIT",
            reference_id=application.application_id,
            description=f"صرف للطلب: {application.application_id}",
            executor_id=executor_id,
            balance_after=self._balances[fund],
            application_id=application.application_id,
        )
        self._transactions.append(txn)
        application.status = ApplicationStatus.DISBURSED
        application.add_audit_entry(
            action="DISBURSED",
            actor=executor_id,
            notes=f"تم الصرف: {application.approved_amount:,.2f} ريال",
        )
        return (
            True,
            f"تم صرف {application.approved_amount:,.2f} ريال من {fund.value}",
        )

    def get_balance(self, fund_type: FundType) -> float:
        """الاستعلام عن رصيد صندوق."""
        return self._balances[fund_type]

    def get_financial_report(self) -> Dict[str, Any]:
        """
        إنشاء تقرير مالي شامل.

        المخرجات:
            قاموس التقرير المالي.
        """
        total_in  = sum(t.amount for t in self._transactions if t.transaction_type == "CREDIT")
        total_out = sum(t.amount for t in self._transactions if t.transaction_type == "DEBIT")
        return {
            "report_date":        date.today().isoformat(),
            "balances":           {f.value: self._balances[f] for f in FundType},
            "total_received":     total_in,
            "total_disbursed":    total_out,
            "total_transactions": len(self._transactions),
            "total_donors":       len(self._donors),
        }

    def get_transactions(
        self,
        fund_type: Optional[FundType] = None,
        limit: int = 20,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> List[Transaction]:
        """
        استرجاع سجل العمليات مع إمكانية التصفية المتقدمة.

        المدخلات:
            fund_type:  الصندوق للتصفية (اختياري).
            limit:      عدد العمليات القصوى.
            from_date:  أول تاريخ للتصفية (اختياري).
            to_date:    آخر تاريخ للتصفية (اختياري).

        المخرجات:
            قائمة العمليات مرتبة من الأحدث للأقدم.
        """
        txns = self._transactions
        if fund_type:
            txns = [t for t in txns if t.fund_type == fund_type]
        if from_date:
            txns = [t for t in txns if t.timestamp.date() >= from_date]
        if to_date:
            txns = [t for t in txns if t.timestamp.date() <= to_date]
        return txns[-limit:]

    def generate_impact_report(
        self,
        donor_phone: str,
        applications: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        تقرير الأثر الفوري للمتبرع بناءً على رقم هاتفه.

        يبحث في سجل المعاملات عن كل تبرعات هذا الرقم، ثم يُقابلها
        بالطلبات المرتبطة (إن وُجدت) ليُخبر المتبرع بالأثر الحقيقي
        الذي صنعه تبرعه على أرض الواقع.

        المدخلات:
            donor_phone: رقم هاتف المتبرع.
            applications: قاموس الطلبات {application_id: Application}
                          من SmartCharityEcosystem._all_applications (اختياري).

        المخرجات:
            رسالة نصية موجزة بأثر التبرع.
        """
        donor_txns = [
            t for t in self._transactions
            if t.transaction_type == "CREDIT" and t.reference_id == donor_phone
        ]
        if not donor_txns:
            return f"لا توجد تبرعات مسجّلة للرقم: {donor_phone}"

        total = sum(t.amount for t in donor_txns)
        lines: List[str] = [
            f"إجمالي تبرعاتك: {total:,.2f} ريال عبر {len(donor_txns)} عملية"
        ]
        for txn in donor_txns:
            if txn.application_id and applications:
                app = applications.get(txn.application_id)
                if app and hasattr(app, "status"):
                    if app.status.value == ApplicationStatus.DISBURSED.value:
                        lines.append(
                            f"✅ تبرعك ساهم في إنجاز: {app.description[:80]}"
                        )
                    else:
                        lines.append(
                            f"⏳ تبرعك مرتبط بطلب قيد المعالجة: {app.application_id}"
                        )
            else:
                lines.append(
                    f"• {txn.amount:,.2f} ريال — {txn.timestamp.strftime('%Y/%m/%d')} "
                    f"({txn.fund_type.value})"
                )
        return "\n".join(lines)

    # ── واجهات متوافقة مع المواصفات (Spec-compatible API) ─────────────────────

    def add_fund(self, fund_type: str, amount: float, source: str) -> bool:
        """
        إضافة أموال إلى الحساب المخصص.

        المدخلات:
            fund_type: نوع الصندوق (قيمة FundType.value).
            amount: المبلغ (ريال).
            source: مصدر التبرع.

        المخرجات:
            True عند النجاح.
        """
        try:
            ft = FundType(fund_type)
        except ValueError:
            self._logger.error("نوع الصندوق غير صالح: %s", fund_type)
            return False
        if amount <= 0:
            return False
        self._balances[ft] += amount
        self._transactions.append(Transaction(
            fund_type=ft,
            amount=amount,
            transaction_type="CREDIT",
            reference_id="",
            description=f"إيداع من: {source}",
            executor_id="SYSTEM",
            balance_after=self._balances[ft],
        ))
        return True

    def deduct_fund(self, fund_type: str, amount: float, purpose: str) -> bool:
        """
        صرف مبلغ من الحساب المخصص مع التأكد من كفاية الرصيد.

        المدخلات:
            fund_type: نوع الصندوق (قيمة FundType.value).
            amount: المبلغ المطلوب صرفه (ريال).
            purpose: الغرض من الصرف.

        المخرجات:
            True عند النجاح، False إذا كان الرصيد غير كافٍ.
        """
        try:
            ft = FundType(fund_type)
        except ValueError:
            self._logger.error("نوع الصندوق غير صالح: %s", fund_type)
            return False
        if amount <= 0 or self._balances[ft] < amount:
            self._logger.warning(
                "رصيد غير كافٍ في %s: المطلوب %.2f | المتاح %.2f",
                fund_type, amount, self._balances[ft],
            )
            return False
        self._balances[ft] -= amount
        self._transactions.append(Transaction(
            fund_type=ft,
            amount=amount,
            transaction_type="DEBIT",
            reference_id="",
            description=f"صرف: {purpose}",
            executor_id="SYSTEM",
            balance_after=self._balances[ft],
        ))
        return True


# ═══════════════════════════════════════════════════════════════════════════════
#  القسم السابع: القطاعات التشغيلية
# ═══════════════════════════════════════════════════════════════════════════════

class BaseSector(ABC):
    """
    الكلاس الأساسي المجرّد للقطاعات التشغيلية.

    يوفر:
        - إدارة دورة حياة الطلبات.
        - توليد تقارير KPI.
    """

    def __init__(self, sector_type: SectorType) -> None:
        """
        تهيئة القطاع.

        المدخلات:
            sector_type: نوع القطاع.
        """
        self.sector_type   = sector_type
        self._applications: List[Application] = []
        self._logger        = logging.getLogger(self.__class__.__name__)

    def submit_application(self, application: Application) -> None:
        """
        تقديم طلب للقطاع.

        المدخلات:
            application: نموذج الطلب.

        الاستثناءات:
            ValueError: إذا كان الطلب لا ينتمي لهذا القطاع.
        """
        if application.sector != self.sector_type:
            raise ValueError(
                f"الطلب يخص {application.sector.value} لا {self.sector_type.value}"
            )
        application.status = ApplicationStatus.SUBMITTED
        application.add_audit_entry(
            action="SUBMITTED",
            actor="SYSTEM",
            notes=f"قُدِّم في قطاع {self.sector_type.value}",
        )
        self._applications.append(application)

    def get_applications(
        self, status: Optional[ApplicationStatus] = None
    ) -> List[Application]:
        """
        استرجاع طلبات القطاع مع إمكانية التصفية.

        المدخلات:
            status: حالة الطلب (اختياري).

        المخرجات:
            قائمة الطلبات.
        """
        if status:
            return [a for a in self._applications if a.status == status]
        return self._applications.copy()

    def generate_kpi_report(self) -> KPIReport:
        """
        توليد تقرير مؤشرات الأداء.

        المخرجات:
            نموذج KPIReport.
        """
        approved = [
            a for a in self._applications
            if a.status in (ApplicationStatus.APPROVED, ApplicationStatus.DISBURSED)
        ]
        rejected = [
            a for a in self._applications
            if a.status == ApplicationStatus.REJECTED
        ]
        return KPIReport(
            sector=self.sector_type,
            report_date=date.today(),
            total_applications=len(self._applications),
            approved_applications=len(approved),
            rejected_applications=len(rejected),
            total_disbursed=sum(a.approved_amount for a in approved),
            beneficiaries_served=len({a.beneficiary_id for a in approved}),
        )

    @abstractmethod
    def get_sector_specific_info(self) -> Dict[str, Any]:
        """استرجاع الإحصائيات الخاصة بالقطاع."""


class HealthSector(BaseSector):
    """
    قطاع الصحة: إدارة طلبات العلاج والأدوية والمستلزمات الطبية.

    المسؤوليات:
        - تغطية تكاليف العلاج والعمليات.
        - توفير الأدوية والأجهزة الطبية.
        - ضمان التوافق مع المعايير الصحية.
    """

    MEDICAL_CATEGORIES = [
        "علاج مستشفى", "أدوية مزمنة", "عمليات جراحية",
        "أجهزة طبية", "علاج نفسي", "أسنان وعيون",
    ]

    def __init__(self) -> None:
        super().__init__(SectorType.HEALTH)

    def get_sector_specific_info(self) -> Dict[str, Any]:
        """إحصائيات قطاع الصحة."""
        return {
            "sector":             self.sector_type.value,
            "medical_categories": self.MEDICAL_CATEGORIES,
            "total_applications": len(self._applications),
            "emergency_cases":    sum(
                1 for a in self._applications
                if a.priority == Priority.CRITICAL
            ),
        }


class HousingSector(BaseSector):
    """
    قطاع الإسكان: دعم الإيجار والترميم وضمان ملاءمة المسكن.

    المسؤوليات:
        - دعم الإيجار للأسر العاجزة.
        - تمويل الترميم والصيانة الضرورية.
        - التحقق من حالة المسكن.
    """

    HOUSING_TYPES = ["إيجار", "ترميم", "إنشاء", "تأهيل"]

    def __init__(self) -> None:
        super().__init__(SectorType.HOUSING)

    def get_sector_specific_info(self) -> Dict[str, Any]:
        """إحصائيات قطاع الإسكان."""
        return {
            "sector":             self.sector_type.value,
            "housing_types":      self.HOUSING_TYPES,
            "total_applications": len(self._applications),
        }


class RecyclingSector(BaseSector):
    """
    قطاع التدوير والاستدامة: استقبال التبرعات العينية وإعادة تأهيلها.

    المسؤوليات:
        - استلام وفرز التبرعات العينية (أثاث وأجهزة).
        - إعادة التأهيل وتوزيع المستفيدين أو تحويلها لقيمة مالية.
        - تقليل الهدر وتعظيم الاستفادة.
    """

    def __init__(self) -> None:
        super().__init__(SectorType.RECYCLING)
        self._inventory: List[Dict[str, Any]] = []

    def add_in_kind_donation(
        self,
        item_name: str,
        quantity: int,
        condition: str,
        donor_name: str,
    ) -> str:
        """
        إضافة تبرع عيني لمستودع التدوير.

        المدخلات:
            item_name: اسم الصنف.
            quantity: الكمية.
            condition: الحالة (ممتاز/جيد/يحتاج صيانة).
            donor_name: اسم المتبرع.

        المخرجات:
            معرّف الصنف في المستودع.
        """
        item_id = "ITEM-" + str(uuid.uuid4())[:6].upper()
        self._inventory.append({
            "item_id":       item_id,
            "name":          item_name,
            "quantity":      quantity,
            "condition":     condition,
            "donor":         donor_name,
            "status":        "في المستودع",
            "received_date": date.today().isoformat(),
        })
        return item_id

    def get_sector_specific_info(self) -> Dict[str, Any]:
        """إحصائيات قطاع التدوير."""
        statuses = ["في المستودع", "موزَّع", "يُعاد تأهيله"]
        return {
            "sector":                self.sector_type.value,
            "total_inventory_items": len(self._inventory),
            "total_applications":    len(self._applications),
            "items_by_status":       {
                s: sum(1 for i in self._inventory if i["status"] == s)
                for s in statuses
            },
        }


class FoodSector(BaseSector):
    """
    قطاع الإطعام وحفظ النعمة: السلال الغذائية والوجبات وتقليل الهدر.

    المسؤوليات:
        - إدارة السلال الغذائية الشهرية.
        - ضمان سلامة الغذاء ومطابقته للمعايير.
        - تقليل هدر الطعام لأدنى نسبة ممكنة.
    """

    FOOD_SAFETY_COLD_MAX_TEMP: int = 5    # °م — الحد الأقصى للتبريد
    FOOD_SAFETY_HOT_MIN_TEMP:  int = 60   # °م — الحد الأدنى للتقديم الساخن

    def __init__(self) -> None:
        super().__init__(SectorType.FOOD)
        self._food_batches: List[Dict[str, Any]] = []
        self._waste_log:    List[Dict[str, Any]] = []

    def register_food_batch(
        self,
        description: str,
        quantity_kg: float,
        expiry_date: date,
        storage_temp: float,
    ) -> Tuple[bool, str]:
        """
        تسجيل دفعة غذائية مع التحقق من سلامة الغذاء.

        المدخلات:
            description: وصف الدفعة.
            quantity_kg: الكمية (كجم).
            expiry_date: تاريخ الانتهاء.
            storage_temp: درجة حرارة التخزين (°م).

        المخرجات:
            (success, message).
        """
        if storage_temp > self.FOOD_SAFETY_COLD_MAX_TEMP:
            return False, (
                f"تحذير سلامة الغذاء: {storage_temp}°م "
                f"تتجاوز الحد المسموح {self.FOOD_SAFETY_COLD_MAX_TEMP}°م"
            )
        if expiry_date < date.today():
            return False, "لا يُقبل غذاء منتهي الصلاحية"

        batch_id = "BATCH-" + str(uuid.uuid4())[:6].upper()
        self._food_batches.append({
            "batch_id":    batch_id,
            "description": description,
            "quantity_kg": quantity_kg,
            "expiry_date": expiry_date.isoformat(),
            "storage_temp": storage_temp,
            "status":      "متاح",
        })
        return True, f"تم تسجيل الدفعة {batch_id}: {quantity_kg} كجم"

    def log_food_waste(
        self, batch_id: str, wasted_kg: float, reason: str
    ) -> None:
        """
        تسجيل هدر الطعام لمتابعة النسب وتقليلها.

        المدخلات:
            batch_id: معرّف الدفعة.
            wasted_kg: الكمية المهدرة (كجم).
            reason: سبب الهدر.
        """
        self._waste_log.append({
            "batch_id":  batch_id,
            "wasted_kg": wasted_kg,
            "reason":    reason,
            "log_date":  date.today().isoformat(),
        })

    def get_waste_rate(self) -> float:
        """
        حساب نسبة الهدر الإجمالية.

        المخرجات:
            نسبة الهدر المئوية.
        """
        total_in    = sum(b["quantity_kg"] for b in self._food_batches)
        total_waste = sum(w["wasted_kg"]   for w in self._waste_log)
        if total_in == 0:
            return 0.0
        return (total_waste / total_in) * 100

    def get_sector_specific_info(self) -> Dict[str, Any]:
        """إحصائيات قطاع الإطعام."""
        return {
            "sector":               self.sector_type.value,
            "total_food_batches":   len(self._food_batches),
            "total_applications":   len(self._applications),
            "waste_rate_%":         round(self.get_waste_rate(), 2),
            "waste_records":        len(self._waste_log),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  القسم الثامن: المنظومة الرئيسية
# ═══════════════════════════════════════════════════════════════════════════════

class SmartCharityEcosystem:
    """
    المنظومة الرئيسية التي تجمع وتنسّق جميع المكونات.

    تربط:
        - SmartAI: نواة الذكاء الاصطناعي.
        - GovernanceSystem: الحوكمة والصلاحيات.
        - FinanceSystem: النظام المالي.
        - القطاعات الأربعة: الصحة، الإسكان، التدوير، الإطعام.
    """

    VERSION           = "1.0.0"
    ORGANIZATION_NAME = "منظومة العمل الخيري الذكي"
    FAST_TRACK_LIMIT  = 5_000.0

    def __init__(self) -> None:
        """تهيئة المنظومة وجميع مكوناتها."""
        self._logger = self._configure_logging()
        self.ai         = SmartAI()
        self.governance = GovernanceSystem()
        self.finance    = FinanceSystem()
        self.sectors: Dict[SectorType, BaseSector] = {
            SectorType.HEALTH:    HealthSector(),
            SectorType.HOUSING:   HousingSector(),
            SectorType.RECYCLING: RecyclingSector(),
            SectorType.FOOD:      FoodSector(),
        }
        self._beneficiaries:     Dict[str, Beneficiary]  = {}
        self._all_applications:  Dict[str, Application]  = {}

    @staticmethod
    def _configure_logging() -> logging.Logger:
        """تهيئة نظام السجلات."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(name)-22s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        return logging.getLogger("SmartCharityEcosystem")

    def register_beneficiary(
        self, beneficiary: Beneficiary
    ) -> Tuple[bool, str]:
        """
        تسجيل مستفيد جديد مع التحقق من أهليته.

        المدخلات:
            beneficiary: نموذج بيانات المستفيد.

        المخرجات:
            (is_eligible, reason).
        """
        is_eligible, reason = self.ai.check_eligibility(beneficiary)
        beneficiary.is_eligible      = is_eligible
        beneficiary.eligibility_notes = reason
        self._beneficiaries[beneficiary.beneficiary_id] = beneficiary
        return is_eligible, reason

    def submit_application(
        self, application: Application
    ) -> Tuple[bool, str]:
        """
        تقديم طلب مساعدة مع التحليل الذكي الفوري.

        المدخلات:
            application: نموذج الطلب.

        المخرجات:
            (success, message).
        """
        beneficiary = self._beneficiaries.get(application.beneficiary_id)
        if not beneficiary:
            return False, "المستفيد غير مسجّل في النظام"
        if not beneficiary.is_eligible:
            return False, f"المستفيد غير مؤهل: {beneficiary.eligibility_notes}"

        score, priority, recommendation = self.ai.analyze_application(
            application, beneficiary
        )
        application.ai_score          = score
        application.priority          = priority
        application.ai_recommendation = recommendation
        application.status            = ApplicationStatus.AI_ANALYZED

        self.sectors[application.sector].submit_application(application)
        self._all_applications[application.application_id] = application

        # ── مسار الطوارئ السريع: اعتماد وصرف تلقائي للحالات الحرجة ──────────
        if (
            application.priority == Priority.CRITICAL
            and application.requested_amount <= self.FAST_TRACK_LIMIT
            and self.finance.get_balance(application.fund_type)
                >= application.requested_amount
        ):
            self.governance.fast_track_approve(
                application, application.requested_amount
            )
            ok, _ = self.finance.disburse_funds(application, "FAST-TRACK-SYSTEM")
            if ok:
                return True, (
                    f"[⚡ طوارئ] {application.application_id} — "
                    f"اعتماد وصرف تلقائي. {recommendation}"
                )

        return True, (
            f"تم تقديم {application.application_id} بنجاح. {recommendation}"
        )

    def process_approval(
        self,
        application_id: str,
        approver_id: str,
        approved_amount: float,
        notes: str = "",
    ) -> Tuple[bool, str]:
        """
        معالجة الموافقة على طلب.

        المدخلات:
            application_id: معرّف الطلب.
            approver_id: معرّف الموافق.
            approved_amount: المبلغ المعتمد.
            notes: ملاحظات.

        المخرجات:
            (success, message).
        """
        application = self._all_applications.get(application_id)
        if not application:
            return False, f"الطلب {application_id} غير موجود"
        if not self.governance.approve_application(
            application, approver_id, approved_amount, notes
        ):
            return False, "فشلت الموافقة — تحقق من صلاحيات الموافق"
        return True, f"تمت الموافقة على الطلب {application_id}"

    def process_disbursement(
        self, application_id: str, executor_id: str
    ) -> Tuple[bool, str]:
        """
        صرف الأموال لطلب معتمد.

        المدخلات:
            application_id: معرّف الطلب.
            executor_id: معرّف منفّذ الصرف.

        المخرجات:
            (success, message).
        """
        application = self._all_applications.get(application_id)
        if not application:
            return False, f"الطلب {application_id} غير موجود"
        return self.finance.disburse_funds(application, executor_id)

    def get_ecosystem_report(self) -> Dict[str, Any]:
        """
        تقرير شامل عن أداء المنظومة الكاملة.

        المخرجات:
            قاموس التقرير الشامل.
        """
        sector_kpis = {}
        for stype, sector in self.sectors.items():
            kpi = sector.generate_kpi_report()
            sector_kpis[stype.value] = {
                "total_applications":   kpi.total_applications,
                "approved_applications": kpi.approved_applications,
                "rejected_applications": kpi.rejected_applications,
                "total_disbursed":       kpi.total_disbursed,
                "approval_rate":         kpi.approval_rate,
                "beneficiaries_served":  kpi.beneficiaries_served,
            }
        return {
            "organization":           self.ORGANIZATION_NAME,
            "version":                self.VERSION,
            "report_date":            date.today().isoformat(),
            "total_beneficiaries":    len(self._beneficiaries),
            "eligible_beneficiaries": sum(
                1 for b in self._beneficiaries.values() if b.is_eligible
            ),
            "total_applications":     len(self._all_applications),
            "financial_report":       self.finance.get_financial_report(),
            "ai_summary":             self.ai.get_experience_summary(),
            "sector_kpis":            sector_kpis,
        }

    def archive_beneficiary(
        self, beneficiary_id: str, actor_id: str = "SYSTEM"
    ) -> bool:
        """
        أرشفة مستفيد (حذف ناعم).

        يُبقي السجل في القاعدة ولكن يُخفيه من التقارير والعمليات الجديدة.

        المدخلات:
            beneficiary_id: معرّف المستفيد.
            actor_id: معرّف منفّذ الأرشفة.

        المخرجات:
            True  عند النجاح، False إذا لم يُوجد المستفيد.
        """
        b = self._beneficiaries.get(beneficiary_id)
        if not b:
            return False
        b.is_archived = True
        self.governance._record_audit(
            action="BENEFICIARY_ARCHIVED",
            actor=actor_id,
            details=f"أُرشف المستفيد: {b.full_name} [{beneficiary_id}]",
        )
        return True

    def restore_beneficiary(
        self, beneficiary_id: str, actor_id: str = "SYSTEM"
    ) -> bool:
        """
        استعادة مستفيد مؤرشف.

        المخرجات:
            True عند النجاح، False إذا لم يُوجد المستفيد.
        """
        b = self._beneficiaries.get(beneficiary_id)
        if not b:
            return False
        b.is_archived = False
        self.governance._record_audit(
            action="BENEFICIARY_RESTORED",
            actor=actor_id,
            details=f"استُعيد المستفيد: {b.full_name} [{beneficiary_id}]",
        )
        return True

    def get_beneficiary_history(
        self, beneficiary_id: str
    ) -> Dict[str, Any]:
        """
        ملف المستفيد الكامل: بياناته + جميع طلباته + إجمالي ما صُرف له.

        المدخلات:
            beneficiary_id: معرّف المستفيد.

        المخرجات:
            قاموس يحتوي على:
                - beneficiary: كائن المستفيد (أو None).
                - applications: قائمة طلباته مرتبة بالتاريخ.
                - total_disbursed: إجمالي ما صُرف له.
                - disbursed_count: عدد مرات الصرف.
                - last_activity: تاريخ آخر طلب (أو None).
        """
        b    = self._beneficiaries.get(beneficiary_id)
        apps = [
            a for a in self._all_applications.values()
            if a.beneficiary_id == beneficiary_id
        ]
        apps.sort(key=lambda a: a.submission_date)
        disbursed = [a for a in apps if a.status == ApplicationStatus.DISBURSED]
        total_dis = sum(a.approved_amount for a in disbursed)
        last_act  = apps[-1].submission_date if apps else None
        return {
            "beneficiary":     b,
            "applications":    apps,
            "total_disbursed": total_dis,
            "disbursed_count": len(disbursed),
            "last_activity":   last_act,
        }

    def generate_impact_report(self, transaction_id: str) -> str:
        """
        تقرير الأثر الفوري للمتبرع: ربط التبرع بنتيجته على أرض الواقع.

        يبحث عن الطلب المرتبط بالتبرع، فإذا كانت حالته DISBURSED يُعلم
        المتبرع بالأثر الفوري الذي صنعه تبرعه المخصص.

        المدخلات:
            transaction_id: معرّف عملية التبرع (CREDIT).

        المخرجات:
            رسالة نصية تُعلم المتبرع بأثر تبرعه.
        """
        txn = next(
            (t for t in self.finance._transactions
             if t.transaction_id == transaction_id),
            None,
        )
        if not txn:
            return f"العملية {transaction_id} غير موجودة"
        if txn.transaction_type != "CREDIT":
            return "هذه العملية ليست تبرعاً، ثمة حسابات تحتاج عملية CREDIT"

        if not txn.application_id:
            return (
                f"شكراً لتبرعك بـ {txn.amount:,.2f} ريال "
                f"بتاريخ {txn.timestamp.strftime('%Y/%m/%d')}م. "
                f"تبرعك في صندوق {txn.fund_type.value} سيصل إلى مستحقيه."
            )

        app = self._all_applications.get(txn.application_id)
        if not app:
            return (
                f"تم تسجيل تبرعك بـ {txn.amount:,.2f} ريال، "
                f"غير أن الطلب المرتبط ({txn.application_id}) لم يُوجد."
            )

        if app.status == ApplicationStatus.DISBURSED:
            ben   = self._beneficiaries.get(app.beneficiary_id)
            name  = ben.full_name if ben else "المستفيد"
            d     = app.approval_date or date.today()
            hijri = HijriCalendar.format_hijri(d.year, d.month, d.day)
            return (
                f"🌟 أثرك الفوري | تبرعك بـ {txn.amount:,.2f} ريال أسهم في "
                f"صرف {app.approved_amount:,.2f} ريال لـ {name} "
                f"عبر قطاع {app.sector.value}. "
                f"تاريخ الصرف: {d}م — {hijri} 🤲"
            )

        return (
            f"تبرعك بـ {txn.amount:,.2f} ريال مرتبط بالطلب {txn.application_id} "
            f"(الحالة: {app.status.value}). سيُصرف فور اكتمال إجراءات الاعتماد."
        )

    def load_demo_data(self) -> None:
        """
        تحميل بيانات تمثيلية شاملة لأغراض العرض والتوضيح.

        يُنشئ: مستخدمين، تبرعات، مستفيدين، وطلبات في القطاعات الأربعة.
        """
        # ── تسجيل المستخدمين ─────────────────────────────────────────────
        self.admin_id = self.governance.register_user(
            "محمد العمري", UserRole.EXECUTIVE_DIR, "الإدارة العليا"
        )
        self.finance_mgr_id = self.governance.register_user(
            "سارة الزهراني", UserRole.FINANCE_MGR, "المالية"
        )
        self.sector_mgr_id = self.governance.register_user(
            "خالد المطيري", UserRole.SECTOR_MGR, "الخدمات الاجتماعية"
        )
        self.case_worker_id = self.governance.register_user(
            "فاطمة الشهري", UserRole.CASE_WORKER, "الخدمات الاجتماعية"
        )

        # ── استلام التبرعات ───────────────────────────────────────────────
        for name, phone, amount, fund in [
            ("عبدالله الراشد", "0501112222", 50_000,  FundType.ZAKAT),
            ("نورة السالم",    "0502223333", 30_000,  FundType.SADAQAT),
            ("شركة الخير",     "0503334444", 100_000, FundType.ZAKAT),
            ("أحمد الحربي",    "0504445555", 20_000,  FundType.AWQAF),
            ("مؤسسة الرحمة",   "0505556666", 15_000,  FundType.RESTRICTED),
        ]:
            self.finance.receive_donation(name, phone, amount, fund, self.admin_id)

        # ── تسجيل المستفيدين ──────────────────────────────────────────────
        beneficiaries = [
            Beneficiary(
                full_name="أم عمر الغامدي",
                national_id="1012345678",
                phone="0511112222",
                address=Address("الرياض", "العزيزية"),
                family_size=6,
                monthly_income=1_800.0,
            ),
            Beneficiary(
                full_name="حسن القرني",
                national_id="1023456789",
                phone="0522223333",
                address=Address("جدة", "البغدادية"),
                family_size=4,
                monthly_income=2_500.0,
                is_employed=True,
                has_disability=True,
            ),
            Beneficiary(
                full_name="مريم الدوسري",
                national_id="1034567890",
                phone="0533334444",
                address=Address("الدمام", "الفيصلية"),
                family_size=3,
                monthly_income=800.0,
            ),
            Beneficiary(
                full_name="عمر السبيعي",
                national_id="1045678901",
                phone="0544445555",
                address=Address("مكة المكرمة", "العزيزية"),
                family_size=8,
                monthly_income=3_000.0,
                is_employed=True,
            ),
        ]
        eligible_ids: List[str] = []
        for ben in beneficiaries:
            ok, _ = self.register_beneficiary(ben)
            if ok:
                eligible_ids.append(ben.beneficiary_id)

        # ── تقديم الطلبات وتشغيل دورة الحياة الكاملة ─────────────────────
        if len(eligible_ids) >= 1:
            app1 = Application(
                beneficiary_id=eligible_ids[0],
                sector=SectorType.HEALTH,
                requested_amount=8_000,
                fund_type=FundType.ZAKAT,
                description="تغطية تكاليف عملية جراحية عاجلة لكسر في الفقرات",
                supporting_docs=["تقرير طبي", "فاتورة المستشفى"],
            )
            self.submit_application(app1)
            self.process_approval(
                app1.application_id, self.sector_mgr_id, 7_500,
                "موافقة بعد المراجعة الطبية"
            )
            self.process_disbursement(app1.application_id, self.finance_mgr_id)

        if len(eligible_ids) >= 2:
            app2 = Application(
                beneficiary_id=eligible_ids[1],
                sector=SectorType.HOUSING,
                requested_amount=12_000,
                fund_type=FundType.SADAQAT,
                description="دعم إيجار منزل لأسرة بحاجة لمسكن مناسب",
                supporting_docs=["عقد الإيجار", "صورة الهوية"],
            )
            self.submit_application(app2)
            self.process_approval(
                app2.application_id, self.sector_mgr_id, 10_000
            )

        if len(eligible_ids) >= 3:
            app3 = Application(
                beneficiary_id=eligible_ids[2],
                sector=SectorType.FOOD,
                requested_amount=1_200,
                fund_type=FundType.SADAQAT,
                description="سلة غذائية شهرية لأسرة من ثلاثة أفراد",
                supporting_docs=["بطاقة العائلة"],
            )
            self.submit_application(app3)
            self.process_approval(
                app3.application_id, self.case_worker_id, 1_200
            )
            self.process_disbursement(app3.application_id, self.finance_mgr_id)

        # ── تبرعات عينية ─────────────────────────────────────────────────
        recycling = self.sectors[SectorType.RECYCLING]
        recycling.add_in_kind_donation("ثلاجة",          2, "جيد",            "خالد العتيبي")
        recycling.add_in_kind_donation("غسالة",          1, "يحتاج صيانة",   "شركة الأمانة")
        recycling.add_in_kind_donation("أثاث غرفة نوم", 3, "ممتاز",          "نورة الأحمد")

        # ── دفعات غذائية ─────────────────────────────────────────────────
        food = self.sectors[SectorType.FOOD]
        food.register_food_batch(
            "تمر وحبوب", 150.0, date.today() + timedelta(days=180), 3.0
        )
        food.register_food_batch(
            "خضروات وفواكه", 80.0, date.today() + timedelta(days=7), 2.0
        )
        food.log_food_waste("BATCH-DEMO", 4.0, "تلف خلال النقل")


# ═══════════════════════════════════════════════════════════════════════════════
#  القسم التاسع: طبقة حفظ واستعادة البيانات
# ═══════════════════════════════════════════════════════════════════════════════

class DataPersistence:
    """
    طبقة حفظ واستعادة بيانات المنظومة بصيغة JSON.

    المسؤوليات:
        - تحويل كائنات المنظومة إلى JSON والعكس.
        - حفظ المستفيدين والطلبات والعمليات المالية والأرصدة.
        - استعادة الجلسة السابقة عند التشغيل.
    """

    DATA_FILE: str = "charity_data.json"

    def __init__(self, tenant_id: str = "default") -> None:
        """تهيئة طبقة الاستمرارية مع عزل بيانات المستأجر."""
        self.tenant_id = tenant_id
        if tenant_id != "default":
            self.DATA_FILE = f"charity_data_{tenant_id}.json"

    @staticmethod
    def _ser_enum(val: Any) -> Any:
        """تحويل قيمة Enum إلى نص."""
        return val.value if isinstance(val, Enum) else val

    @staticmethod
    def _ben_to_dict(b: Beneficiary) -> Dict:
        """تحويل كائن Beneficiary إلى قاموس قابل للتسلسل."""
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
            "is_archived":      b.is_archived,
            "zakat_category":   b.zakat_category.value if b.zakat_category else None,
            "registration_date": str(b.registration_date),
            "tenant_id":        b.tenant_id,
        }

    @staticmethod
    def _dict_to_ben(d: Dict) -> Beneficiary:
        """استعادة كائن Beneficiary من قاموس."""
        b = Beneficiary(
            full_name=d["full_name"],
            national_id=d["national_id"],
            phone=d["phone"],
            address=Address(city=d["city"], district=d["district"]),
            family_size=d["family_size"],
            monthly_income=d["monthly_income"],
            is_employed=d["is_employed"],
            has_disability=d["has_disability"],
        )
        b.beneficiary_id = d["beneficiary_id"]
        b.is_eligible    = d["is_eligible"]
        b.is_archived    = d.get("is_archived", False)
        b.tenant_id      = d.get("tenant_id", "default")
        if d.get("zakat_category"):
            b.zakat_category = ZakatCategory(d["zakat_category"])
        return b

    @staticmethod
    def _app_to_dict(a: Application) -> Dict:
        """تحويل كائن Application إلى قاموس قابل للتسلسل."""
        return {
            "application_id":     a.application_id,
            "beneficiary_id":     a.beneficiary_id,
            "sector":             a.sector.value,
            "requested_amount":   a.requested_amount,
            "approved_amount":    a.approved_amount,
            "fund_type":          a.fund_type.value,
            "status":             a.status.value,
            "priority":           a.priority.value,
            "description":        a.description,
            "supporting_docs":    a.supporting_docs,
            "submission_date":    str(a.submission_date),
            "ai_score":           a.ai_score,
            "ai_recommendation":  a.ai_recommendation,
            "approver_id":        a.approver_id,
            "audit_trail":        a.audit_trail,
            "tenant_id":          a.tenant_id,
        }

    @staticmethod
    def _dict_to_app(d: Dict) -> Application:
        """استعادة كائن Application من قاموس."""
        a = Application(
            beneficiary_id=d["beneficiary_id"],
            sector=SectorType(d["sector"]),
            requested_amount=d["requested_amount"],
            fund_type=FundType(d["fund_type"]),
            description=d["description"],
            supporting_docs=d.get("supporting_docs", []),
        )
        a.application_id    = d["application_id"]
        a.approved_amount   = d["approved_amount"]
        a.status            = ApplicationStatus(d["status"])
        a.priority          = Priority(d["priority"])
        a.ai_score          = d["ai_score"]
        a.ai_recommendation = d.get("ai_recommendation", "")
        a.approver_id       = d.get("approver_id", "")
        a.audit_trail       = d.get("audit_trail", [])
        a.tenant_id         = d.get("tenant_id", "default")
        return a

    @staticmethod
    def _txn_to_dict(t: Transaction) -> Dict:
        """تحويل كائن Transaction إلى قاموس قابل للتسلسل."""
        return {
            "transaction_id":   t.transaction_id,
            "fund_type":        t.fund_type.value,
            "amount":           t.amount,
            "transaction_type": t.transaction_type,
            "description":      t.description,
            "executor_id":      t.executor_id,
            "timestamp":        str(t.timestamp),
            "reference_id":     t.reference_id,
            "balance_after":    t.balance_after,
            "tenant_id":        t.tenant_id,
            "application_id":   t.application_id,
        }

    @staticmethod
    def _dict_to_txn(d: Dict) -> Transaction:
        """استعادة كائن Transaction من قاموس."""
        t = Transaction(
            fund_type=FundType(d["fund_type"]),
            amount=d["amount"],
            transaction_type=d["transaction_type"],
            description=d["description"],
            executor_id=d.get("executor_id", "SYSTEM"),
            reference_id=d.get("reference_id", ""),
            balance_after=d.get("balance_after", 0.0),
        )
        t.transaction_id = d["transaction_id"]
        t.timestamp      = datetime.fromisoformat(d["timestamp"]) if d.get("timestamp") else datetime.now()
        t.tenant_id      = d.get("tenant_id", "default")
        t.application_id = d.get("application_id")
        return t

    def save(self, eco: "SmartCharityEcosystem") -> Tuple[bool, str]:
        """
        حفظ حالة المنظومة الكاملة إلى ملف JSON.

        المدخلات:
            eco: مثيل المنظومة الرئيسية.

        المخرجات:
            (نجح, رسالة)
        """
        try:
            snapshot = {
                "version":       SmartCharityEcosystem.VERSION,
                "saved_at":      datetime.now().isoformat(),
                "beneficiaries": [
                    self._ben_to_dict(b)
                    for b in eco._beneficiaries.values()
                ],
                "applications":  [
                    self._app_to_dict(a)
                    for a in eco._all_applications.values()
                ],
                "transactions":  [
                    self._txn_to_dict(t)
                    for t in eco.finance._transactions
                ],
                "balances": {
                    ft.value: eco.finance._balances[ft]
                    for ft in FundType
                },
                "donors": [
                    {
                        "donor_id":       d.donor_id,
                        "full_name":      d.full_name,
                        "phone":          d.phone,
                        "fund_type":      d.fund_type.value,
                        "total_donated":  d.total_donated,
                        "donation_count": d.donation_count,
                        "tenant_id":      d.tenant_id,
                    }
                    for d in eco.finance._donors.values()
                ],
            }
            base = os.path.dirname(os.path.abspath(
                globals().get("__file__", os.getcwd())
            ))
            path = os.path.join(base, self.DATA_FILE)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(snapshot, fh, ensure_ascii=False, indent=2, default=str)
            return True, f"تم الحفظ في: {path}"
        except Exception as exc:
            return False, f"فشل الحفظ: {exc}"

    def load(self, eco: "SmartCharityEcosystem") -> Tuple[bool, str]:
        """
        تحميل الحالة المحفوظة من ملف JSON إلى المنظومة.

        المدخلات:
            eco: مثيل المنظومة الرئيسية.

        المخرجات:
            (نجح, رسالة)
        """
        base = os.path.dirname(os.path.abspath(
            globals().get("__file__", os.getcwd())
        ))
        path = os.path.join(base, self.DATA_FILE)
        if not os.path.exists(path):
            return False, "لا يوجد ملف حفظ سابق"
        try:
            with open(path, encoding="utf-8") as fh:
                snapshot = json.load(fh)

            for d in snapshot.get("beneficiaries", []):
                b = self._dict_to_ben(d)
                eco._beneficiaries[b.beneficiary_id] = b

            for d in snapshot.get("applications", []):
                a = self._dict_to_app(d)
                eco._all_applications[a.application_id] = a
                if a.sector in eco.sectors:
                    eco.sectors[a.sector]._applications.append(a)

            eco.finance._transactions = [
                self._dict_to_txn(d) for d in snapshot.get("transactions", [])
            ]
            for ft_val, bal in snapshot.get("balances", {}).items():
                eco.finance._balances[FundType(ft_val)] = float(bal)

            eco.finance._donors = {}
            for d in snapshot.get("donors", []):
                dr = DonorRecord(
                    full_name=d.get("full_name", d.get("name", "")),
                    phone=d.get("phone", ""),
                    fund_type=FundType(d.get("fund_type", FundType.ZAKAT.value)),
                )
                dr.donor_id       = d.get("donor_id", dr.donor_id)
                dr.total_donated  = float(d.get("total_donated", d.get("total_given", 0.0)))
                dr.donation_count = int(d.get("donation_count", 0))
                dr.tenant_id      = d.get("tenant_id", "default")
                key = f"{dr.phone}_{dr.fund_type.value}"
                eco.finance._donors[key] = dr

            count_b = len(snapshot.get("beneficiaries", []))
            count_a = len(snapshot.get("applications", []))
            return True, f"تم تحميل {count_b} مستفيد و{count_a} طلب"
        except Exception as exc:
            return False, f"فشل التحميل: {exc}"


# ═══════════════════════════════════════════════════════════════════════════════
#  القسم العاشر: واجهة المستخدم النصية
# ═══════════════════════════════════════════════════════════════════════════════

class CLI:
    """
    واجهة المستخدم النصية التفاعلية لمنظومة العمل الخيري الذكي.

    توفر ثلاث مجموعات من الخيارات:
        - العمليات التفاعلية: تسجيل مستفيدين، تبرعات، طلبات، موافقات، صرف.
        - البيانات: بحث، حفظ، تصدير تقرير.
        - التقارير والمتابعة: تقارير شاملة، مالية، قطاعية، تدقيق، تنبؤات.
    """

    def __init__(self, ecosystem: SmartCharityEcosystem) -> None:
        """
        تهيئة الواجهة.

        المدخلات:
            ecosystem: مثيل المنظومة الرئيسية.
        """
        self.eco        = ecosystem
        self.persistence = DataPersistence()

    @staticmethod
    def _col_letter(n: int) -> str:
        """تحويل رقم العمود (0-based) إلى حرف Excel (A, B, ..., Z, AA, ...)."""
        s, n = "", n + 1
        while n:
            n, r = divmod(n - 1, 26)
            s = chr(65 + r) + s
        return s

    @staticmethod
    def _build_xlsx(
        sheets: List[Tuple[str, List[str], List[List]]]
    ) -> bytes:
        """
        بناء ملف XLSX حقيقي باستخدام zipfile فقط (بدون مكتبات خارجية).

        المدخلات:
            sheets: قائمة من (اسم_الورقة, رؤوس_الأعمدة, صفوف_البيانات).

        المخرجات:
            bytes — محتوى ملف XLSX صالح لفتحه في Excel.
        """
        ss:    List[str]      = []
        ss_id: Dict[str, int] = {}

        def _si(v: Any) -> int:
            t = str(v)
            if t not in ss_id:
                ss_id[t] = len(ss)
                ss.append(t)
            return ss_id[t]

        def _esc(s: str) -> str:
            return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                         .replace(">", "&gt;").replace('"', "&quot;"))

        sheets_xml: List[str] = []
        for _, headers, rows in sheets:
            lines = [
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<worksheet xmlns="http://schemas.openxmlformats.org/'
                'spreadsheetml/2006/main">',
                '<sheetData>',
            ]
            hcells = "".join(
                f'<c r="{CLI._col_letter(i)}1" t="s" s="1">'
                f'<v>{_si(h)}</v></c>'
                for i, h in enumerate(headers)
            )
            lines.append(f'<row r="1">{hcells}</row>')
            for ri, row in enumerate(rows, 2):
                cells = ""
                for ci, val in enumerate(row):
                    col = CLI._col_letter(ci)
                    sv  = str(val)
                    try:
                        float(sv.replace(",", ""))
                        cells += (
                            f'<c r="{col}{ri}">'
                            f'<v>{_esc(sv)}</v></c>'
                        )
                    except ValueError:
                        cells += (
                            f'<c r="{col}{ri}" t="s">'
                            f'<v>{_si(sv)}</v></c>'
                        )
                lines.append(f'<row r="{ri}">{cells}</row>')
            lines += ["</sheetData>", "</worksheet>"]
            sheets_xml.append("\n".join(lines))

        ss_body = "".join(
            f'<si><t xml:space="preserve">{_esc(s)}</t></si>' for s in ss
        )
        ss_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            f' count="{len(ss)}" uniqueCount="{len(ss)}">'
            f'{ss_body}</sst>'
        )
        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/'
            'spreadsheetml/2006/main">'
            '<fonts count="2">'
            '<font><sz val="11"/><name val="Calibri"/></font>'
            '<font><b/><sz val="11"/><name val="Calibri"/></font>'
            '</fonts>'
            '<fills count="2">'
            '<fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill>'
            '</fills>'
            '<borders count="1">'
            '<border><left/><right/><top/><bottom/><diagonal/></border>'
            '</borders>'
            '<cellStyleXfs count="1">'
            '<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>'
            '</cellStyleXfs>'
            '<cellXfs count="2">'
            '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"'
            ' applyFont="1"/>'
            '</cellXfs>'
            '</styleSheet>'
        )
        n  = len(sheets)
        sh = "".join(
            f'<sheet name="{_esc(nm)}" sheetId="{i+1}" r:id="rId{i+1}"/>'
            for i, (nm, _, _) in enumerate(sheets)
        )
        wb_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/'
            'spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats'
            '.org/officeDocument/2006/relationships">'
            f'<sheets>{sh}</sheets></workbook>'
        )
        NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        NS_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
        wb_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{NS_PKG}">'
            + "".join(
                f'<Relationship Id="rId{i+1}" '
                f'Type="{NS_REL}/worksheet" '
                f'Target="worksheets/sheet{i+1}.xml"/>'
                for i in range(n)
            )
            + f'<Relationship Id="rId{n+1}" Type="{NS_REL}/sharedStrings"'
            f' Target="sharedStrings.xml"/>'
            + f'<Relationship Id="rId{n+2}" Type="{NS_REL}/styles"'
            f' Target="styles.xml"/>'
            + '</Relationships>'
        )
        root_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{NS_PKG}">'
            f'<Relationship Id="rId1" Type="{NS_REL}/officeDocument"'
            f' Target="xl/workbook.xml"/>'
            f'</Relationships>'
        )
        NS_CT = "http://schemas.openxmlformats.org/package/2006/content-types"
        NS_SS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        sh_ct = "".join(
            f'<Override PartName="/xl/worksheets/sheet{i+1}.xml"'
            f' ContentType="application/vnd.openxmlformats-officedocument'
            f'.spreadsheetml.worksheet+xml"/>'
            for i in range(n)
        )
        ct_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Types xmlns="{NS_CT}">'
            '<Default Extension="rels" ContentType="application/vnd'
            '.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application'
            '/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + sh_ct
            + '<Override PartName="/xl/sharedStrings.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument.spreadsheetml'
            '.sharedStrings+xml"/>'
            '<Override PartName="/xl/styles.xml" ContentType="application'
            '/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '</Types>'
        )
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml",          ct_xml)
            zf.writestr("_rels/.rels",                  root_rels)
            zf.writestr("xl/workbook.xml",              wb_xml)
            zf.writestr("xl/_rels/workbook.xml.rels",   wb_rels)
            zf.writestr("xl/styles.xml",                styles_xml)
            zf.writestr("xl/sharedStrings.xml",         ss_xml)
            for i, xml in enumerate(sheets_xml):
                zf.writestr(f"xl/worksheets/sheet{i+1}.xml", xml)
        return buf.getvalue()

    @staticmethod
    def _build_pdf_html(eco: SmartCharityEcosystem) -> str:
        """
        بناء صفحة HTML منسّقة RTL جاهزة للطباعة كـ PDF.

        تحتوي على: غلاف + بطاقات ملخص + ثلاثة جداول بيانات.
        عند الفتح في المتصفح تُفتح نافذة الطباعة تلقائياً.
        """
        def _esc(s: str) -> str:
            return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                         .replace(">", "&gt;"))

        def _tbl(title: str, hdrs: List[str], rows: List[List]) -> str:
            ths = "".join(f"<th>{_esc(h)}</th>" for h in hdrs)
            trs = "".join(
                "<tr>" + "".join(f"<td>{_esc(v)}</td>" for v in row) + "</tr>"
                for row in rows
            )
            return (
                f'<section class="sec"><h2>{_esc(title)}</h2>'
                f'<table><thead><tr>{ths}</tr></thead>'
                f'<tbody>{trs}</tbody></table></section>'
            )

        today   = datetime.now().strftime("%Y/%m/%d  %H:%M")
        tot_bal = sum(eco.finance.get_balance(ft) for ft in FundType)

        ben_rows = [
            [b.beneficiary_id, b.full_name, b.address.city,
             b.family_size, f"{b.monthly_income:,.0f}",
             "نعم" if b.is_eligible else "لا"]
            for b in eco._beneficiaries.values()
        ]
        app_rows = [
            [a.application_id, a.sector.value, f"{a.requested_amount:,.0f}",
             f"{a.approved_amount:,.0f}", a.status.value, a.priority.value]
            for a in eco._all_applications.values()
        ]
        txn_rows = [
            [t.transaction_id, t.fund_type.value, f"{t.amount:,.2f}",
             t.transaction_type, str(t.timestamp)[:10]]
            for t in eco.finance.get_transactions(limit=300)
        ]

        css = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
       direction: rtl; font-size: 12px; color: #222; background: #fff; padding: 20px; }
.cover { text-align: center; padding: 40px 0 28px;
         border-bottom: 3px solid #1a6b3c; margin-bottom: 26px; }
.cover h1 { font-size: 22px; color: #1a6b3c; }
.cover .sub { color: #666; margin-top: 6px; }
.cards { display: flex; gap: 14px; margin-bottom: 26px; }
.card { flex: 1; border: 1px solid #c8e6d0; border-radius: 8px;
        padding: 14px; text-align: center; background: #f5fbf7; }
.card .val { font-size: 20px; font-weight: bold; color: #1a6b3c; }
.card .lbl { color: #666; font-size: 11px; margin-top: 4px; }
.sec { margin-bottom: 26px; }
.sec h2 { background: #1a6b3c; color: #fff; padding: 7px 12px;
           border-radius: 4px 4px 0 0; font-size: 13px; }
table { width: 100%; border-collapse: collapse; font-size: 11px; }
th { background: #e6f2eb; color: #1a6b3c; padding: 6px 8px;
     border: 1px solid #b8d8c4; font-weight: bold; }
td { padding: 5px 8px; border: 1px solid #ddd; }
tr:nth-child(even) td { background: #f8fdf9; }
.footer { text-align: center; margin-top: 24px; color: #999;
          font-size: 10px; border-top: 1px solid #ddd; padding-top: 10px; }
@media print {
  body { padding: 0; }
  .sec { page-break-inside: avoid; }
  tr { page-break-inside: avoid; }
}"""

        body = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head>
<meta charset="UTF-8">
<title>تقرير منظومة العمل الخيري</title>
<style>{css}</style>
</head><body>
<div class="cover">
  <h1>🕌 منظومة العمل الخيري الذكي</h1>
  <div class="sub">تقرير شامل — {today}</div>
</div>
<div class="cards">
  <div class="card">
    <div class="val">{len(eco._beneficiaries)}</div>
    <div class="lbl">إجمالي المستفيدين</div>
  </div>
  <div class="card">
    <div class="val">{len(eco._all_applications)}</div>
    <div class="lbl">إجمالي الطلبات</div>
  </div>
  <div class="card">
    <div class="val">{tot_bal:,.0f} ﷼</div>
    <div class="lbl">إجمالي الأرصدة</div>
  </div>
</div>
{_tbl(f"المستفيدون ({len(ben_rows)})",
      ["المعرّف","الاسم","المدينة","الأسرة","الدخل","مؤهل"], ben_rows)}
{_tbl(f"الطلبات ({len(app_rows)})",
      ["المعرّف","القطاع","مطلوب","معتمد","الحالة","الأولوية"], app_rows)}
{_tbl(f"المعاملات (آخر {len(txn_rows)})",
      ["المعرّف","الصندوق","المبلغ","النوع","التاريخ"], txn_rows)}
<div class="footer">
  تم إنشاؤه بواسطة منظومة العمل الخيري الذكي — {today}
</div>
<script>
window.addEventListener('load',function(){{setTimeout(function(){{window.print();}},800);}});
</script>
</body></html>"""
        return body

    def _export_csv_interactive(self) -> None:
        """
        تصدير بيانات المنظومة إلى CSV أو Excel أو PDF.

        الصيغ المدعومة:
            1 — CSV  (.csv)  — يفتح في أي برنامج جداول.
            2 — Excel (.xlsx) — يفتح في Microsoft Excel مع دعم العربية.
            3 — PDF  — HTML جاهز للطباعة يُفتح في المتصفح تلقائياً.
            4 — الثلاثة معاً.
        """
        Printer.header("📋 تصدير البيانات (CSV / Excel / PDF)")

        fmt_ops = [
            ("1", "📊", "CSV  (.csv)   — يفتح في Excel / LibreOffice"),
            ("2", "📗", "Excel (.xlsx) — يفتح في Microsoft Excel"),
            ("3", "📄", "PDF  — HTML يُطبَع من المتصفح (Ctrl+P)"),
            ("4", "🗂️", "الثلاثة معاً"),
        ]
        for k, ic, lb in fmt_ops:
            print(f"  {Colors.MAGENTA}[{k}]{Colors.RESET}  {ic}  {lb}")
        Printer.divider()
        fmt = self._prompt("نوع الملف", "2")

        print(f"\n  {Colors.CYAN}ماذا تُصدِّر؟{Colors.RESET}")
        data_ops = [
            ("A", "المستفيدون"),
            ("B", "الطلبات"),
            ("C", "المعاملات المالية"),
            ("D", "الثلاثة معاً"),
        ]
        for k, lb in data_ops:
            print(f"  {Colors.GREEN}[{k}]{Colors.RESET}  {lb}")
        Printer.divider()
        sel = self._prompt("اختر البيانات", "D").upper()

        try:
            base = os.path.dirname(os.path.abspath(
                globals().get("__file__", os.getcwd())
            ))
        except Exception:
            base = os.getcwd()

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exported: List[tuple] = []

        # ── تجهيز البيانات ───────────────────────────────────────────
        BEN_HDR = [
            "معرّف المستفيد", "الاسم", "رقم الهوية", "الهاتف",
            "المدينة", "حجم الأسرة", "الدخل الشهري",
            "إعاقة", "مؤهل", "فئة الزكاة", "تاريخ التسجيل",
        ]
        ben_rows = [
            [
                b.beneficiary_id, b.full_name, b.national_id, b.phone,
                b.address.city, b.family_size, b.monthly_income,
                "نعم" if b.has_disability else "لا",
                "نعم" if b.is_eligible else "لا",
                b.zakat_category.value if b.zakat_category else "",
                str(b.registration_date),
            ]
            for b in self.eco._beneficiaries.values()
        ]
        APP_HDR = [
            "معرّف الطلب", "معرّف المستفيد", "القطاع", "الصندوق",
            "المبلغ المطلوب", "المبلغ المعتمد", "الحالة", "الأولوية",
            "نقاط الذكاء", "تاريخ التقديم",
        ]
        app_rows = [
            [
                a.application_id, a.beneficiary_id, a.sector.value,
                a.fund_type.value, a.requested_amount, a.approved_amount,
                a.status.value, a.priority.value,
                f"{a.ai_score:.1f}", str(a.submission_date),
            ]
            for a in self.eco._all_applications.values()
        ]
        TXN_HDR = [
            "معرّف العملية", "نوع الصندوق", "المبلغ", "النوع",
            "الوصف", "المنفّذ", "الرصيد بعد العملية", "التوقيت",
        ]
        txn_rows = [
            [
                t.transaction_id, t.fund_type.value, t.amount,
                t.transaction_type, t.description, t.executor_id,
                f"{t.balance_after:.2f}", str(t.timestamp)[:19],
            ]
            for t in self.eco.finance.get_transactions(limit=9_999)
        ]
        sheets_map: Dict[str, List[Tuple[str, List, List]]] = {
            "A": [("المستفيدون", BEN_HDR, ben_rows)],
            "B": [("الطلبات",    APP_HDR, app_rows)],
            "C": [("المعاملات",  TXN_HDR, txn_rows)],
            "D": [
                ("المستفيدون", BEN_HDR, ben_rows),
                ("الطلبات",    APP_HDR, app_rows),
                ("المعاملات",  TXN_HDR, txn_rows),
            ],
        }
        sheets = sheets_map.get(sel, sheets_map["D"])

        # ── CSV ──────────────────────────────────────────────────────
        if fmt in ("1", "4"):
            for name, hdrs, rows in sheets:
                path = os.path.join(base, f"{name}_{stamp}.csv")
                with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                    w = csv.writer(fh)
                    w.writerow(hdrs)
                    w.writerows(rows)
                exported.append((f"CSV: {name} ({len(rows)} سجل)", path))

        # ── Excel ─────────────────────────────────────────────────────
        if fmt in ("2", "4"):
            fname = f"report_{sel}_{stamp}.xlsx"
            path  = os.path.join(base, fname)
            with open(path, "wb") as fh:
                fh.write(CLI._build_xlsx(sheets))
            total = sum(len(r) for _, _, r in sheets)
            exported.append(
                (f"Excel: {len(sheets)} ورقة ({total} سجل إجمالاً)", path)
            )

        # ── PDF (HTML) ────────────────────────────────────────────────
        if fmt in ("3", "4"):
            import webbrowser
            fname = f"report_{stamp}.html"
            path  = os.path.join(base, fname)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(CLI._build_pdf_html(self.eco))
            exported.append(("PDF HTML: تقرير شامل", path))
            webbrowser.open(f"file:///{path.replace(chr(92), '/')}")
            Printer.info(
                "فُتح في المتصفح — اضغط Ctrl+P ← اختر 'Microsoft Print to PDF'"
            )

        Printer.divider()
        if exported:
            Printer.success("اكتمل التصدير:")
            for label, path in exported:
                Printer.kv(label, path)
        else:
            Printer.warning("لم يُصدَّر شيء")

    # ══════════════════════════════════════════════════════════════════════
    #  ✏️  وظائف التعديل
    # ══════════════════════════════════════════════════════════════════════

    def _edit_record_interactive(self) -> None:
        """
        تعديل أي سجل موجود في المنظومة.

        الأنواع المدعومة:
            1 — مستفيد  : الاسم / الهاتف / المدينة / الأسرة / الدخل / الإعاقة.
            2 — طلب مساعدة : الوصف / المبلغ / الأولوية (قبل المعالجة).
            3 — متبرع   : الاسم / الهاتف.
        """
        Printer.header("✏️ تعديل سجل موجود")
        ops = [
            ("1", "👤", "مستفيد"),
            ("2", "📋", "طلب مساعدة"),
            ("3", "💰", "متبرع"),
        ]
        for k, ic, lb in ops:
            print(f"  {Colors.CYAN}[{k}]{Colors.RESET}  {ic}  {lb}")
        Printer.divider()
        rec_type = self._prompt("نوع السجل", "1")
        if rec_type == "1":
            self._edit_beneficiary_interactive()
        elif rec_type == "2":
            self._edit_application_interactive()
        elif rec_type == "3":
            self._edit_donor_interactive()
        else:
            Printer.warning("اختيار غير صالح")

    def _edit_beneficiary_interactive(self) -> None:
        """تعديل سجل مستفيد — يدعم البحث بالمعرّف أو الاسم أو رقم الهوية."""
        Printer.section("✏️ تعديل مستفيد")
        query = self._prompt("ابحث بالمعرّف أو الاسم أو رقم الهوية", "")
        if not query:
            return
        ql = query.lower()
        matches = [
            b for b in self.eco._beneficiaries.values()
            if ql in b.beneficiary_id.lower()
            or ql in b.full_name
            or ql in b.national_id
            or ql in b.phone
        ]
        if not matches:
            Printer.warning(f"لا توجد نتائج لـ: {query}")
            return
        if len(matches) > 1:
            for i, b in enumerate(matches, 1):
                print(
                    f"  {Colors.CYAN}[{i}]{Colors.RESET}  "
                    f"{b.beneficiary_id}  {b.full_name}"
                )
            Printer.divider()
            idx = self._prompt("اختر رقم", "1")
            try:
                b = matches[int(idx) - 1]
            except (ValueError, IndexError):
                Printer.warning("اختيار غير صالح")
                return
        else:
            b = matches[0]

        Printer.section(f"تعديل: {b.full_name}  [{b.beneficiary_id}]")
        Printer.info("اضغط Enter للإبقاء على القيمة الحالية")
        print()

        b.full_name        = self._prompt("الاسم الكامل",       b.full_name)
        b.phone            = self._prompt("الهاتف",              b.phone)
        b.national_id      = self._prompt("رقم الهوية",          b.national_id)
        b.address.city     = self._prompt("المدينة",             b.address.city)
        b.address.district = self._prompt("الحي",                b.address.district)

        fs = self._prompt("حجم الأسرة", str(b.family_size))
        try:
            b.family_size = max(1, int(fs))
        except ValueError:
            pass

        inc = self._prompt("الدخل الشهري (ريال)", str(b.monthly_income))
        try:
            b.monthly_income = max(0.0, float(inc))
        except ValueError:
            pass

        dis = self._prompt(
            "ذوي إعاقة؟ (1=نعم / 0=لا)",
            "1" if b.has_disability else "0",
        )
        b.has_disability = (dis.strip() == "1")

        is_elig, reason = self.eco.ai.check_eligibility(b)
        b.is_eligible        = is_elig
        b.eligibility_notes  = reason

        self.eco.governance._record_audit(
            action="BENEFICIARY_EDITED",
            actor="CLI",
            details=f"تعديل بيانات: {b.full_name} [{b.beneficiary_id}]",
        )
        Printer.success(
            f"تم تحديث [{b.full_name}] — "
            f"الأهلية: {'مؤهل ✓' if is_elig else 'غير مؤهل ✗'}"
        )

    def _edit_application_interactive(self) -> None:
        """تعديل طلب مساعدة — الوصف/المبلغ/الأولوية (قبل المعالجة فقط)."""
        Printer.section("✏️ تعديل طلب")
        query = self._prompt("معرّف الطلب أو معرّف المستفيد", "")
        if not query:
            return
        ql = query.lower()
        matches = [
            a for a in self.eco._all_applications.values()
            if ql in a.application_id.lower()
            or ql in a.beneficiary_id.lower()
        ]
        if not matches:
            Printer.warning(f"لا توجد نتائج لـ: {query}")
            return
        if len(matches) > 1:
            for i, a in enumerate(matches, 1):
                print(
                    f"  {Colors.CYAN}[{i}]{Colors.RESET}  "
                    f"{a.application_id}  {a.sector.value}  "
                    f"{a.status.value}"
                )
            Printer.divider()
            idx = self._prompt("اختر رقم", "1")
            try:
                a = matches[int(idx) - 1]
            except (ValueError, IndexError):
                Printer.warning("اختيار غير صالح")
                return
        else:
            a = matches[0]

        Printer.section(
            f"تعديل: {a.application_id}  |  الحالة: {a.status.value}"
        )
        Printer.info("اضغط Enter للإبقاء على القيمة الحالية")
        print()

        a.description = self._prompt("الوصف", a.description)

        editable = (
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.AI_ANALYZED,
        )
        if a.status in editable:
            amt = self._prompt(
                "المبلغ المطلوب (ريال)", str(a.requested_amount)
            )
            try:
                a.requested_amount = max(0.0, float(amt))
            except ValueError:
                pass

            pri_vals = " | ".join(p.value for p in Priority)
            print(f"\n  الأولويات المتاحة: {Colors.DIM}{pri_vals}{Colors.RESET}")
            pri = self._prompt("الأولوية", a.priority.value)
            try:
                a.priority = Priority(pri)
            except ValueError:
                Printer.warning(f"قيمة غير معروفة: {pri} — لم تُغيَّر الأولوية")
        else:
            Printer.warning(
                f"حالة [{a.status.value}] — لا يُسمح بتعديل المبلغ أو الأولوية"
            )

        a.add_audit_entry(
            action="EDITED", actor="CLI",
            notes=f"تعديل بيانات الطلب",
        )
        self.eco.governance._record_audit(
            action="APPLICATION_EDITED",
            actor="CLI",
            details=f"تعديل بيانات: {a.application_id} | الحالة: {a.status.value}",
        )
        Printer.success(f"تم تحديث الطلب {a.application_id}")

    def _edit_donor_interactive(self) -> None:
        """تعديل سجل متبرع — الاسم والهاتف مع إعادة فهرسة المفتاح."""
        Printer.section("✏️ تعديل متبرع")
        query = self._prompt("ابحث بالاسم أو الهاتف", "")
        if not query:
            return
        matches = [
            d for d in self.eco.finance._donors.values()
            if query in d.full_name or query in d.phone
        ]
        if not matches:
            Printer.warning(f"لا توجد نتائج لـ: {query}")
            return
        if len(matches) > 1:
            for i, d in enumerate(matches, 1):
                print(
                    f"  {Colors.CYAN}[{i}]{Colors.RESET}  "
                    f"{d.full_name}  {d.phone}  |  "
                    f"{d.total_donated:,.0f} ريال"
                )
            Printer.divider()
            idx = self._prompt("اختر رقم", "1")
            try:
                d = matches[int(idx) - 1]
            except (ValueError, IndexError):
                Printer.warning("اختيار غير صالح")
                return
        else:
            d = matches[0]

        Printer.section(
            f"تعديل: {d.full_name}  |  إجمالي التبرعات: "
            f"{d.total_donated:,.0f} ريال"
        )
        Printer.info("اضغط Enter للإبقاء على القيمة الحالية")
        print()

        old_phone  = d.phone
        d.full_name = self._prompt("الاسم الكامل", d.full_name)
        new_phone   = self._prompt("الهاتف",       d.phone)

        if new_phone != old_phone:
            old_key = f"{old_phone}_{d.fund_type.value}"
            new_key = f"{new_phone}_{d.fund_type.value}"
            d.phone = new_phone
            self.eco.finance._donors.pop(old_key, None)
            self.eco.finance._donors[new_key] = d

        Printer.success(f"تم تحديث سجل {d.full_name}")

    # ══════════════════════════════════════════════════════════════════════
    #  🗑️  إلغاء وأرشفة   |   📖  ملف المستفيد الكامل
    # ══════════════════════════════════════════════════════════════════════

    def _archive_cancel_interactive(self) -> None:
        """
        إلغاء طلب مساعدة أو أرشفة مستفيد (حذف ناعم مع توثيق).

        الخيارات:
            1 — إلغاء طلب   : يغيّر الحالة إلى CANCELLED ويوثّق في Audit.
            2 — أرشفة مستفيد: يضع is_archived=True ويُخفيه من التقارير.
            3 — استعادة مؤرشف: إعادة تفعيل مستفيد مؤرشف.
        """
        Printer.header("🗑️ إلغاء / أرشفة")
        ops = [
            ("1", "❌", "إلغاء طلب مساعدة"),
            ("2", "📦", "أرشفة مستفيد (إخفاء)"),
            ("3", "♻️",  "استعادة مستفيد مؤرشف"),
        ]
        for k, ic, lb in ops:
            print(f"  {Colors.CYAN}[{k}]{Colors.RESET}  {ic}  {lb}")
        Printer.divider()
        choice = self._prompt("الخيار", "1")

        if choice == "1":
            query = self._prompt("معرّف الطلب أو معرّف المستفيد", "")
            if not query:
                return
            ql = query.lower()
            matches = [
                a for a in self.eco._all_applications.values()
                if ql in a.application_id.lower()
                or ql in a.beneficiary_id.lower()
            ]
            if not matches:
                Printer.warning(f"لا توجد نتائج لـ: {query}")
                return
            if len(matches) > 1:
                for i, a in enumerate(matches, 1):
                    print(
                        f"  {Colors.CYAN}[{i}]{Colors.RESET}  "
                        f"{a.application_id}  {a.sector.value}  "
                        f"{a.status.value}"
                    )
                Printer.divider()
                idx = self._prompt("اختر رقم", "1")
                try:
                    a = matches[int(idx) - 1]
                except (ValueError, IndexError):
                    Printer.warning("اختيار غير صالح")
                    return
            else:
                a = matches[0]
            reason = self._prompt("سبب الإلغاء (اختياري)", "")
            ok = self.eco.governance.cancel_application(a, "CLI", reason)
            if ok:
                Printer.success(f"تم إلغاء الطلب {a.application_id}")
            else:
                Printer.warning(
                    f"لا يمكن إلغاء طلب بحالة [{a.status.value}]"
                )

        elif choice in ("2", "3"):
            query = self._prompt("ابحث بالمعرّف أو الاسم", "")
            if not query:
                return
            ql = query.lower()
            matches = [
                b for b in self.eco._beneficiaries.values()
                if ql in b.beneficiary_id.lower() or ql in b.full_name
            ]
            if not matches:
                Printer.warning(f"لا توجد نتائج لـ: {query}")
                return
            if len(matches) > 1:
                for i, b in enumerate(matches, 1):
                    arch = "📦" if b.is_archived else "  "
                    print(
                        f"  {Colors.CYAN}[{i}]{Colors.RESET}  "
                        f"{arch} {b.beneficiary_id}  {b.full_name}"
                    )
                Printer.divider()
                idx = self._prompt("اختر رقم", "1")
                try:
                    b = matches[int(idx) - 1]
                except (ValueError, IndexError):
                    Printer.warning("اختيار غير صالح")
                    return
            else:
                b = matches[0]

            if choice == "2":
                ok = self.eco.archive_beneficiary(b.beneficiary_id, "CLI")
                if ok:
                    Printer.success(f"أُرشف: {b.full_name} — لن يظهر في التقارير")
                else:
                    Printer.error("فشل الأرشفة")
            else:
                ok = self.eco.restore_beneficiary(b.beneficiary_id, "CLI")
                if ok:
                    Printer.success(f"استُعيد: {b.full_name} ✓")
                else:
                    Printer.error("فشل الاستعادة")
        else:
            Printer.warning("اختيار غير صالح")

    def _beneficiary_history_interactive(self) -> None:
        """
        عرض الملف الكامل لمستفيد: بياناته + جميع طلباته + إجمالي ما صُرف له.
        """
        Printer.header("📖 ملف المستفيد الكامل")
        query = self._prompt("ابحث بالمعرّف أو الاسم أو رقم الهوية", "")
        if not query:
            return
        ql = query.lower()
        matches = [
            b for b in self.eco._beneficiaries.values()
            if ql in b.beneficiary_id.lower()
            or ql in b.full_name
            or ql in b.national_id
        ]
        if not matches:
            Printer.warning(f"لا توجد نتائج لـ: {query}")
            return
        if len(matches) > 1:
            for i, b in enumerate(matches, 1):
                arch = " [مؤرشف]" if b.is_archived else ""
                print(
                    f"  {Colors.CYAN}[{i}]{Colors.RESET}  "
                    f"{b.beneficiary_id}  {b.full_name}{arch}"
                )
            Printer.divider()
            idx = self._prompt("اختر رقم", "1")
            try:
                b = matches[int(idx) - 1]
            except (ValueError, IndexError):
                Printer.warning("اختيار غير صالح")
                return
        else:
            b = matches[0]

        hist = self.eco.get_beneficiary_history(b.beneficiary_id)
        apps = hist["applications"]

        Printer.section(f"ملف: {b.full_name}")
        arch_tag = f"  {Colors.RED}[مؤرشف]{Colors.RESET}" if b.is_archived else ""
        Printer.kv("المعرّف",          b.beneficiary_id + arch_tag)
        Printer.kv("رقم الهوية",        b.national_id)
        Printer.kv("الهاتف",            b.phone)
        Printer.kv("المدينة / الحي",    f"{b.address.city} / {b.address.district}")
        Printer.kv("حجم الأسرة",        b.family_size)
        Printer.kv("الدخل الشهري",      f"{b.monthly_income:,.0f} ريال")
        Printer.kv("ذوي إعاقة",         "نعم" if b.has_disability else "لا")
        Printer.kv("الأهلية",           f"{'مؤهل ✓' if b.is_eligible else 'غير مؤهل ✗'}")
        Printer.kv("تاريخ التسجيل",     HijriCalendar.dual(b.registration_date))
        Printer.divider()
        Printer.kv("إجمالي الطلبات",    len(apps))
        Printer.kv("مرات الصرف",        hist["disbursed_count"])
        Printer.kv("إجمالي ما صُرف",    f"{hist['total_disbursed']:,.2f} ريال")
        Printer.kv("آخر نشاط",          HijriCalendar.dual(hist["last_activity"]) if hist["last_activity"] else "—")

        if apps:
            Printer.section(f"الطلبات ({len(apps)})")
            for a in apps:
                status_color = (
                    Colors.GREEN  if a.status == ApplicationStatus.DISBURSED else
                    Colors.RED    if a.status in (ApplicationStatus.REJECTED,
                                                   ApplicationStatus.CANCELLED) else
                    Colors.YELLOW
                )
                print(
                    f"  {Colors.DIM}{HijriCalendar.dual(a.submission_date)}{Colors.RESET}  "
                    f"{a.application_id}  {a.sector.value}  "
                    f"{a.requested_amount:,.0f} ﷼  "
                    f"{status_color}{a.status.value}{Colors.RESET}"
                )

    def _show_startup_alerts(self) -> None:
        """عرض ملخص سريع للتنبيهات فور تحميل البيانات."""
        today   = date.today()
        crit, warn = 0, 0

        LOW = 5_000.0
        for ft in FundType:
            bal = self.eco.finance.get_balance(ft)
            if bal < 1_000:
                crit += 1
            elif bal < LOW:
                warn += 1

        pending_statuses = (
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.AI_ANALYZED,
            ApplicationStatus.PENDING_APPROVAL,
        )
        for a in self.eco._all_applications.values():
            if a.status in pending_statuses:
                age = (today - a.submission_date).days
                if age > 14:
                    crit += 1
                elif age > 7:
                    warn += 1
            if a.priority == Priority.CRITICAL and a.status in pending_statuses:
                crit += 1

        food_sector = self.eco.sectors.get(SectorType.FOOD)
        if food_sector and hasattr(food_sector, "_food_batches"):
            for batch in food_sector._food_batches:
                exp = batch.get("expiry_date")
                if not exp:
                    continue
                if isinstance(exp, str):
                    try:
                        exp = date.fromisoformat(exp)
                    except ValueError:
                        continue
                days_left = (exp - today).days
                if days_left < 0:
                    crit += 1
                elif days_left <= 14:
                    warn += 1

        if crit == 0 and warn == 0:
            Printer.success("فحص التنبيهات: النظام بحالة مثالية ✓")
        else:
            parts = []
            if crit:
                parts.append(
                    f"{Colors.RED}{Colors.BOLD}{crit} حرجة{Colors.RESET}"
                )
            if warn:
                parts.append(
                    f"{Colors.YELLOW}{warn} تحذير{Colors.RESET}"
                )
            print(
                f"  {Colors.BOLD}🔔 تنبيهات:{Colors.RESET}  "
                + "  |  ".join(parts)
                + f"  {Colors.DIM}— اضغط [N] للتفاصيل{Colors.RESET}"
            )
        print()

    def run(self) -> None:
        """تشغيل الواجهة النصية التفاعلية."""
        self._print_welcome()
        ok, msg = self.persistence.load(self.eco)
        if ok:
            Printer.success(f"تم استعادة الجلسة السابقة — {msg}")
        else:
            self.eco.load_demo_data()
            Printer.success("تم تحميل البيانات التمثيلية بنجاح")
        self._show_startup_alerts()

        # العمليات التي تُغيِّر البيانات وتستدعي حفظاً تلقائياً
        _MUTATING = {"A", "B", "C", "D", "E", "P", "R"}

        while True:
            choice = self._show_main_menu()
            if choice == "0":
                ok, msg = self.persistence.save(self.eco)
                (Printer.success if ok else Printer.warning)(msg)
                self._farewell()
                break
            self._handle_choice(choice)
            if choice in _MUTATING:
                ok, _ = self.persistence.save(self.eco)
                if ok:
                    print(
                        f"  {Colors.DIM}💾 حُفظ تلقائياً{Colors.RESET}"
                    )
                else:
                    Printer.warning("تعذَّر الحفظ التلقائي!")

    def _print_welcome(self) -> None:
        """طباعة شاشة الترحيب."""
        os.system("cls" if os.name == "nt" else "clear")
        print(f"""{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║         🌙   منظومة العمل الخيري الذكي   🌙                            ║
║              Smart Charity Ecosystem  v{SmartCharityEcosystem.VERSION}                      ║
║                                                                          ║
║    نظام متكامل لإدارة الزكاة والصدقات والأوقاف بذكاء اصطناعي          ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}""")
        print(f"  {Colors.YELLOW}📅  {HijriCalendar.today_dual()}{Colors.RESET}\n")

    def _show_main_menu(self) -> str:
        """عرض القائمة الرئيسية المزدوجة وإرجاع اختيار المستخدم."""
        Printer.header("القائمة الرئيسية")

        print(f"  {Colors.GREEN}{Colors.BOLD}── العمليات التفاعلية ──────────────────────────{Colors.RESET}")
        ops = [
            ("A", "👤", "تسجيل مستفيد جديد"),
            ("B", "💵", "تسجيل تبرع جديد"),
            ("C", "📝", "تقديم طلب مساعدة"),
            ("D", "✅", "موافقة / رفض طلب"),
            ("E", "💸", "صرف أموال طلب معتمد"),
            ("P", "✏️",  "تعديل سجل موجود (مستفيد / طلب / متبرع)"),
            ("R", "🗑️",  "إلغاء طلب / أرشفة مستفيد"),
            ("H", "📖",  "ملف مستفيد كامل (كل طلباته + ما صُرف له)"),
            ("Z", "💛", "حاسبة الزكاة التفاعلية"),
        ]
        for key, icon, label in ops:
            print(f"  {Colors.GREEN}[{key}]{Colors.RESET}  {icon}  {label}")

        print(f"\n  {Colors.MAGENTA}{Colors.BOLD}── البيانات ────────────────────────────────────{Colors.RESET}")
        data_ops = [
            ("N", "🔔", "لوحة التنبيهات ومراقبة النظام"),
            ("G", "📊", "لوحة الإحصاء والمخططات"),
            ("F", "🔍", "بحث عن مستفيد أو طلب"),
            ("S", "💾", "حفظ البيانات الآن"),
            ("X", "📤", "تصدير تقرير شامل إلى ملف"),
            ("V", "📋", "تصدير البيانات (CSV / Excel / PDF)"),
        ]
        for key, icon, label in data_ops:
            print(f"  {Colors.MAGENTA}[{key}]{Colors.RESET}  {icon}  {label}")

        print(f"\n  {Colors.BLUE}{Colors.BOLD}── التقارير والمتابعة ──────────────────────────{Colors.RESET}")
        reports = [
            ("1", "📊", "التقرير الشامل للمنظومة"),
            ("2", "💰", "التقرير المالي التفصيلي"),
            ("3", "🏥", "قطاع الصحة"),
            ("4", "🏠", "قطاع الإسكان"),
            ("5", "♻️ ", "قطاع التدوير والاستدامة"),
            ("6", "🍽️ ", "قطاع الإطعام وحفظ النعمة"),
            ("7", "🛡️ ", "سجل التدقيق والحوكمة"),
            ("8", "🧠", "ملخص الذكاء الاصطناعي"),
            ("9", "📋", "السياسات والإجراءات المعتمدة"),
            ("T", "🔮", "التنبؤ بالاحتياجات المستقبلية"),
            ("0", "🚪", "خروج (مع حفظ تلقائي)"),
        ]
        for key, icon, label in reports:
            color = Colors.RED if key == "0" else Colors.CYAN
            print(f"  {color}[{key}]{Colors.RESET}  {icon}  {label}")

        print()
        return input(f"  {Colors.YELLOW}اختر العملية: {Colors.RESET}").strip().upper()

    def _handle_choice(self, choice: str) -> None:
        """توجيه اختيار المستخدم للمعالج المناسب."""
        handlers = {
            # ── العمليات التفاعلية ──────────────────────────────────────
            "A": self._register_beneficiary_interactive,
            "B": self._record_donation_interactive,
            "C": self._submit_application_interactive,
            "D": self._process_approval_interactive,
            "E": self._process_disbursement_interactive,
            "P": self._edit_record_interactive,
            "R": self._archive_cancel_interactive,
            "H": self._beneficiary_history_interactive,
            "Z": self._zakat_calculator_interactive,
            # ── البيانات ──────────────────────────────────────────────
            "N": self._show_alerts_dashboard,
            "G": self._show_statistics_dashboard,
            "F": self._search_interactive,
            "S": self._save_data_interactive,
            "X": self._export_report_interactive,
            "V": self._export_csv_interactive,
            # ── التقارير والمتابعة ──────────────────────────────────────
            "1": self._show_ecosystem_report,
            "2": self._show_financial_report,
            "3": lambda: self._show_sector(SectorType.HEALTH),
            "4": lambda: self._show_sector(SectorType.HOUSING),
            "5": lambda: self._show_sector(SectorType.RECYCLING),
            "6": lambda: self._show_sector(SectorType.FOOD),
            "7": self._show_audit_log,
            "8": self._show_ai_summary,
            "9": self._show_policies,
            "T": self._show_predictions,
        }
        handler = handlers.get(choice)
        if handler:
            handler()
        else:
            Printer.warning("اختيار غير صحيح، حاول مجدداً")
        input(f"\n  {Colors.DIM}اضغط Enter للعودة...{Colors.RESET}")

    # ══════════════════════════════════════════════════════════════════════
    #  العمليات التفاعلية
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _prompt(label: str, default: str = "") -> str:
        """
        قراءة إدخال المستخدم مع إظهار قيمة افتراضية اختيارية.

        المدخلات:
            label: نص المطالبة.
            default: القيمة الافتراضية (اختياري).

        المخرجات:
            النص المُدخَل أو القيمة الافتراضية.
        """
        hint = f" [{Colors.DIM}{default}{Colors.RESET}]" if default else ""
        value = input(f"  {Colors.CYAN}{label}{hint}: {Colors.RESET}").strip()
        return value if value else default

    @staticmethod
    def _prompt_float(label: str, default: float = 0.0) -> float:
        """
        قراءة رقم عشري من المستخدم مع معالجة الخطأ.

        المدخلات:
            label: نص المطالبة.
            default: القيمة الافتراضية.

        المخرجات:
            الرقم المُدخَل أو القيمة الافتراضية عند خطأ.
        """
        raw = input(f"  {Colors.CYAN}{label} [{default}]: {Colors.RESET}").strip()
        try:
            return float(raw) if raw else default
        except ValueError:
            Printer.warning(f"قيمة غير صحيحة، سيُستخدم الافتراضي: {default}")
            return default

    @staticmethod
    def _prompt_int(label: str, default: int = 0) -> int:
        """
        قراءة رقم صحيح من المستخدم مع معالجة الخطأ.

        المدخلات:
            label: نص المطالبة.
            default: القيمة الافتراضية.

        المخرجات:
            الرقم المُدخَل أو القيمة الافتراضية عند خطأ.
        """
        raw = input(f"  {Colors.CYAN}{label} [{default}]: {Colors.RESET}").strip()
        try:
            return int(raw) if raw else default
        except ValueError:
            Printer.warning(f"قيمة غير صحيحة، سيُستخدم الافتراضي: {default}")
            return default

    @staticmethod
    def _choose_enum(enum_cls: type, title: str) -> Any:
        """
        عرض قائمة تعداد وإرجاع الاختيار.

        المدخلات:
            enum_cls: كلاس التعداد.
            title: عنوان القائمة.

        المخرجات:
            قيمة التعداد المختارة.
        """
        members = list(enum_cls)
        print(f"\n  {Colors.BLUE}{Colors.BOLD}{title}:{Colors.RESET}")
        for i, member in enumerate(members, start=1):
            print(f"  {Colors.CYAN}[{i}]{Colors.RESET} {member.value}")
        while True:
            raw = input(f"  {Colors.YELLOW}اختر رقماً (1-{len(members)}): {Colors.RESET}").strip()
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(members):
                    return members[idx]
            except ValueError:
                pass
            Printer.warning("اختيار غير صحيح، حاول مجدداً")

    def _register_beneficiary_interactive(self) -> None:
        """
        واجهة تسجيل مستفيد جديد بإدخال تفاعلي كامل.

        تجمع بيانات المستفيد، تُحقق من الأهلية عبر SmartAI،
        وتعرض النتيجة فوراً.
        """
        Printer.header("👤 تسجيل مستفيد جديد")
        print(f"  {Colors.DIM}(اضغط Enter لقبول القيمة الافتراضية حيث ينطبق){Colors.RESET}\n")

        full_name    = self._prompt("الاسم الكامل")
        national_id  = self._prompt("رقم الهوية الوطنية")
        phone        = self._prompt("رقم الجوال")
        city         = self._prompt("المدينة", "الرياض")
        district     = self._prompt("الحي")
        family_size  = self._prompt_int("عدد أفراد الأسرة", 4)
        monthly_income = self._prompt_float("الدخل الشهري (ريال)", 0.0)

        emp_raw = self._prompt("موظف بدخل مستقر؟ (ن/ل)", "ل")
        is_employed = emp_raw.strip() in ("ن", "y", "Y", "yes")

        dis_raw = self._prompt("يعاني من إعاقة؟ (ن/ل)", "ل")
        has_disability = dis_raw.strip() in ("ن", "y", "Y", "yes")

        beneficiary = Beneficiary(
            full_name=full_name,
            national_id=national_id,
            phone=phone,
            address=Address(city=city, district=district),
            family_size=family_size,
            monthly_income=monthly_income,
            is_employed=is_employed,
            has_disability=has_disability,
        )

        eligible, reason = self.eco.register_beneficiary(beneficiary)
        Printer.divider()
        if eligible:
            Printer.success(f"تم التسجيل بنجاح — المعرّف: {beneficiary.beneficiary_id}")
            Printer.kv("حالة الأهلية",  reason)
            Printer.kv("تاريخ التسجيل", HijriCalendar.dual(beneficiary.registration_date))
            if beneficiary.zakat_category:
                Printer.kv("مصرف الزكاة", beneficiary.zakat_category.value)
        else:
            Printer.error(f"لم يُقبل التسجيل: {reason}")
            Printer.kv("المعرّف (للمراجعة)", beneficiary.beneficiary_id)

    def _record_donation_interactive(self) -> None:
        """
        واجهة تسجيل تبرع جديد بإدخال تفاعلي.

        تُودع المبلغ في الصندوق الصحيح وتعرض الرصيد المحدَّث.
        """
        Printer.header("💵 تسجيل تبرع جديد")

        donor_name  = self._prompt("اسم المتبرع")
        donor_phone = self._prompt("هاتف المتبرع")
        amount      = self._prompt_float("قيمة التبرع (ريال)")
        fund_type   = self._choose_enum(FundType, "اختر نوع الصندوق")

        success, msg = self.eco.finance.receive_donation(
            donor_name, donor_phone, amount, fund_type, "CLI-USER"
        )
        Printer.divider()
        if success:
            Printer.success(msg)
            Printer.kv(
                f"الرصيد الحالي لـ {fund_type.value}",
                f"{self.eco.finance.get_balance(fund_type):,.2f} ريال",
            )
        else:
            Printer.error(msg)

    def _submit_application_interactive(self) -> None:
        """
        واجهة تقديم طلب مساعدة جديد بإدخال تفاعلي.

        تُطبّق التحليل الذكي الفوري وتعرض نتيجة التقييم.
        """
        Printer.header("📝 تقديم طلب مساعدة جديد")

        Printer.section("المستفيدون المسجّلون المؤهلون")
        eligible = [
            b for b in self.eco._beneficiaries.values() if b.is_eligible
        ]
        if not eligible:
            Printer.warning("لا يوجد مستفيدون مؤهلون — سجّل مستفيداً أولاً (الخيار A)")
            return
        for b in eligible:
            print(
                f"  {Colors.CYAN}{b.beneficiary_id}{Colors.RESET}  "
                f"{b.full_name:<22}  "
                f"{Colors.DIM}{str(b.address)}{Colors.RESET}"
            )

        Printer.divider()
        ben_id    = self._prompt("أدخل معرّف المستفيد")
        sector    = self._choose_enum(SectorType, "اختر القطاع التشغيلي")
        fund_type = self._choose_enum(FundType, "اختر الصندوق المالي")
        amount    = self._prompt_float("المبلغ المطلوب (ريال)")
        desc      = self._prompt("وصف الحاجة")
        docs_raw  = self._prompt("المستندات المرفقة (افصل بفاصلة)", "")
        docs      = [d.strip() for d in docs_raw.split(",") if d.strip()]

        application = Application(
            beneficiary_id=ben_id,
            sector=sector,
            requested_amount=amount,
            fund_type=fund_type,
            description=desc,
            supporting_docs=docs,
        )
        success, msg = self.eco.submit_application(application)
        Printer.divider()
        if success:
            Printer.success(f"تم التقديم — {application.application_id}")
            Printer.kv("تاريخ التقديم",         HijriCalendar.dual(application.submission_date))
            Printer.kv("نقاط الذكاء الاصطناعي", f"{application.ai_score:.1f} / 100")
            Printer.kv("مستوى الأولوية",        application.priority.name)
            Printer.kv("توصية الذكاء الاصطناعي", application.ai_recommendation)
        else:
            Printer.error(msg)

    def _process_approval_interactive(self) -> None:
        """
        واجهة الموافقة أو الرفض على طلب تفاعلياً.

        تعرض الطلبات المنتظرة وتتحقق من صلاحيات الموافق
        قبل تنفيذ القرار.
        """
        Printer.header("✅ موافقة / رفض طلب")

        pending = [
            a for a in self.eco._all_applications.values()
            if a.status in (
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.AI_ANALYZED,
                ApplicationStatus.PENDING_APPROVAL,
            )
        ]
        if not pending:
            Printer.info("لا توجد طلبات بانتظار الموافقة حالياً")
            return

        Printer.section("الطلبات المنتظرة")
        for app in pending:
            print(
                f"  {Colors.CYAN}{app.application_id}{Colors.RESET}  "
                f"{app.sector.value:<18}  "
                f"{Colors.BOLD}{app.requested_amount:>10,.0f} ريال{Colors.RESET}  "
                f"الأولوية: {app.priority.name}"
            )

        Printer.divider()
        app_id   = self._prompt("أدخل معرّف الطلب")
        decision = self._prompt("القرار: موافقة (م) أم رفض (ر)?", "م")

        if decision in ("م", "m", "M"):
            Printer.section("المستخدمون المؤهلون للموافقة")
            for uid, udata in self.eco.governance._users.items():
                limit = GovernanceSystem.APPROVAL_MATRIX.get(udata["role"], 0)
                limit_str = "غير محدود" if limit == float("inf") else f"{limit:,.0f} ريال"
                print(
                    f"  {Colors.CYAN}{uid}{Colors.RESET}  "
                    f"{udata['name']:<20}  "
                    f"{udata['role'].value:<18}  "
                    f"حد: {limit_str}"
                )
            approver_id     = self._prompt("معرّف الموافق")
            approved_amount = self._prompt_float("المبلغ المعتمد (ريال)")
            notes           = self._prompt("ملاحظات", "")
            success, msg    = self.eco.process_approval(
                app_id, approver_id, approved_amount, notes
            )
        else:
            reason   = self._prompt("سبب الرفض")
            app_obj  = self.eco._all_applications.get(app_id)
            if app_obj:
                self.eco.governance.reject_application(app_obj, "CLI-USER", reason)
                success, msg = True, f"تم رفض الطلب {app_id}"
            else:
                success, msg = False, f"الطلب {app_id} غير موجود"

        Printer.divider()
        (Printer.success if success else Printer.error)(msg)

    def _process_disbursement_interactive(self) -> None:
        """
        واجهة صرف الأموال لطلب معتمد تفاعلياً.

        تعرض الطلبات المعتمدة مع أرصدة الصناديق للتحقق
        قبل تنفيذ عملية الصرف.
        """
        Printer.header("💸 صرف أموال طلب معتمد")

        approved = [
            a for a in self.eco._all_applications.values()
            if a.status == ApplicationStatus.APPROVED
        ]
        if not approved:
            Printer.info("لا توجد طلبات معتمدة بانتظار الصرف")
            return

        Printer.section("الطلبات المعتمدة")
        for app in approved:
            bal = self.eco.finance.get_balance(app.fund_type)
            can = Colors.GREEN if bal >= app.approved_amount else Colors.RED
            print(
                f"  {Colors.CYAN}{app.application_id}{Colors.RESET}  "
                f"{app.fund_type.value:<15}  "
                f"معتمد: {Colors.BOLD}{app.approved_amount:>10,.0f} ريال{Colors.RESET}  "
                f"رصيد الصندوق: {can}{bal:,.0f}{Colors.RESET}"
            )

        Printer.divider()
        app_id      = self._prompt("أدخل معرّف الطلب للصرف")
        executor_id = self._prompt("معرّف منفّذ الصرف", "CLI-USER")
        success, msg = self.eco.process_disbursement(app_id, executor_id)
        Printer.divider()
        (Printer.success if success else Printer.error)(msg)

    def _show_alerts_dashboard(self) -> None:
        """
        لوحة التنبيهات الفورية ومراقبة صحة النظام.

        تفحص وتُبلّغ عن:
            - أرصدة الصناديق المنخفضة.
            - الطلبات المعلّقة منذ أكثر من 7 أيام.
            - دفعات الطعام المنتهية أو القريبة من الانتهاء.
            - الحالات الحرجة في انتظار الموافقة.
            - ملخص الصحة العامة للنظام.
        """
        from datetime import timedelta
        Printer.header("🔔 لوحة التنبيهات ومراقبة النظام")
        print(f"  {Colors.YELLOW}📅  {HijriCalendar.today_dual()}{Colors.RESET}\n")
        today     = date.today()
        alerts: List[Dict] = []

        # ── 1. أرصدة الصناديق المنخفضة ─────────────────────────────────
        LOW_BALANCE_THRESHOLD = 5_000.0
        for ft in FundType:
            bal = self.eco.finance.get_balance(ft)
            if bal < LOW_BALANCE_THRESHOLD:
                alerts.append({
                    "level":   "CRITICAL" if bal < 1_000 else "WARNING",
                    "icon":    "🔴" if bal < 1_000 else "🟡",
                    "category": "رصيد منخفض",
                    "message": f"صندوق [{ft.value}] — الرصيد: {bal:,.0f} ريال",
                })

        # ── 2. طلبات معلّقة أكثر من 7 أيام ────────────────────────────
        pending_statuses = (
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.AI_ANALYZED,
            ApplicationStatus.PENDING_APPROVAL,
        )
        for a in self.eco._all_applications.values():
            if a.status in pending_statuses:
                age = (today - a.submission_date).days
                if age > 7:
                    alerts.append({
                        "level":    "WARNING" if age <= 14 else "CRITICAL",
                        "icon":     "🟡" if age <= 14 else "🔴",
                        "category": "طلب متأخر",
                        "message":  (
                            f"{a.application_id} — {age} يوم انتظاراً | "
                            f"الحالة: {a.status.value}"
                        ),
                    })

        # ── 3. دفعات الطعام المنتهية أو القريبة من الانتهاء ───────────
        food_sector = self.eco.sectors.get(SectorType.FOOD)
        if food_sector and hasattr(food_sector, "_food_batches"):
            for batch in food_sector._food_batches:
                exp = batch.get("expiry_date")
                if not exp:
                    continue
                if isinstance(exp, str):
                    try:
                        exp = date.fromisoformat(exp)
                    except ValueError:
                        continue
                days_left = (exp - today).days
                if days_left < 0:
                    alerts.append({
                        "level":    "CRITICAL",
                        "icon":     "🔴",
                        "category": "دفعة منتهية",
                        "message":  (
                            f"{batch.get('item_name', '—')} — "
                            f"انتهت منذ {abs(days_left)} يوم"
                        ),
                    })
                elif days_left <= 14:
                    alerts.append({
                        "level":    "WARNING",
                        "icon":     "🟡",
                        "category": "تنتهي قريباً",
                        "message":  (
                            f"{batch.get('item_name', '—')} — "
                            f"تنتهي خلال {days_left} يوم"
                        ),
                    })

        # ── 4. حالات حرجة بانتظار الموافقة ────────────────────────────
        critical_pending = [
            a for a in self.eco._all_applications.values()
            if a.priority == Priority.CRITICAL
            and a.status in pending_statuses
        ]
        for a in critical_pending:
            alerts.append({
                "level":    "CRITICAL",
                "icon":     "🆘",
                "category": "حالة حرجة",
                "message":  (
                    f"{a.application_id} — {a.sector.value} | "
                    f"طُلب: {a.requested_amount:,.0f} ريال | "
                    f"انتظار منذ {(today - a.submission_date).days} يوم"
                ),
            })

        # ── 5. عرض التنبيهات ────────────────────────────────────────────
        critical_count = sum(1 for al in alerts if al["level"] == "CRITICAL")
        warning_count  = sum(1 for al in alerts if al["level"] == "WARNING")

        if not alerts:
            Printer.success("لا توجد تنبيهات — النظام يعمل بحالة مثالية ✓")
        else:
            Printer.section(
                f"التنبيهات الحرجة: {critical_count}  |  "
                f"التحذيرات: {warning_count}  |  "
                f"الإجمالي: {len(alerts)}"
            )
            for al in sorted(alerts, key=lambda x: x["level"]):
                clr = Colors.RED if al["level"] == "CRITICAL" else Colors.YELLOW
                print(
                    f"  {al['icon']}  {clr}{al['level']:<10}{Colors.RESET}  "
                    f"{Colors.CYAN}{al['category']:<18}{Colors.RESET}  "
                    f"{al['message']}"
                )

        # ── 6. مؤشر صحة النظام ──────────────────────────────────────────
        Printer.divider()
        Printer.section("مؤشر الصحة العامة للنظام")
        total_b   = len(self.eco._beneficiaries)
        elig_b    = sum(1 for b in self.eco._beneficiaries.values() if b.is_eligible)
        total_a   = len(self.eco._all_applications)
        disbursed = sum(
            1 for a in self.eco._all_applications.values()
            if a.status == ApplicationStatus.DISBURSED
        )
        total_bal = sum(
            self.eco.finance.get_balance(ft) for ft in FundType
        )

        health_score = 100
        health_score -= critical_count * 15
        health_score -= warning_count  * 5
        health_score  = max(0, min(100, health_score))

        if health_score >= 80:
            h_clr, h_lbl = Colors.GREEN,  "ممتاز ✓"
        elif health_score >= 60:
            h_clr, h_lbl = Colors.YELLOW, "جيد — يحتاج متابعة"
        else:
            h_clr, h_lbl = Colors.RED,    "تحتاج تدخلاً عاجلاً"

        print(
            f"\n  مؤشر الصحة: "
            f"{h_clr}{Colors.BOLD}{health_score}/100  {h_lbl}{Colors.RESET}"
        )
        filled = int(health_score / 100 * 40)
        bar = (
            f"{Colors.GREEN}{'█' * filled}"
            f"{Colors.RED}{'░' * (40 - filled)}{Colors.RESET}"
        )
        print(f"  [{bar}]")
        print()
        Printer.kv("إجمالي المستفيدين",        total_b)
        Printer.kv("المؤهلون للمساعدة",        elig_b)
        Printer.kv("إجمالي الطلبات",            total_a)
        Printer.kv("تم صرفها",                  disbursed)
        Printer.kv("إجمالي الأرصدة",
                   f"{total_bal:,.0f} ريال")
        Printer.kv("تنبيهات حرجة",
                   f"{Colors.RED}{critical_count}{Colors.RESET}" if critical_count
                   else f"{Colors.GREEN}لا يوجد{Colors.RESET}")

    def _zakat_calculator_interactive(self) -> None:
        """
        حاسبة الزكاة التفاعلية الشاملة.

        تحسب الزكاة على خمسة أوعية: النقود والودائع، عروض التجارة،
        الذهب والفضة، الزراعة، والأنعام — وفق الفقه الإسلامي.
        """
        Printer.header("💛 حاسبة الزكاة التفاعلية")
        NISAB_SAR   = SmartAI.NISAB_THRESHOLD
        ZAKAT_RATE  = 0.025

        print(f"  {Colors.DIM}نصاب الزكاة الحالي: {NISAB_SAR:,.2f} ريال (معادل 85 جم ذهب){Colors.RESET}\n")

        Printer.section("أدخل ما تملكه في كل وعاء (0 إن لم ينطبق)")

        cash         = self._prompt_float("النقود والأرصدة البنكية (ريال)")
        trade_goods  = self._prompt_float("عروض التجارة — البضائع والمخزون (ريال)")
        gold_grams   = self._prompt_float("الذهب (جرام)")
        silver_grams = self._prompt_float("الفضة (جرام)")
        crops_kg     = self._prompt_float("المحاصيل الزراعية (كيلوجرام)")
        irrigated    = self._prompt("المحاصيل مروية بتكلفة؟ (ن=نعم/ل=لا)", "ل")
        camels       = self._prompt_int("الإبل (رأس)")
        cattle       = self._prompt_int("البقر والجاموس (رأس)")
        sheep        = self._prompt_int("الغنم والماعز (رأس)")

        GOLD_PRICE_PER_GRAM   = 230.0
        SILVER_PRICE_PER_GRAM = 3.0
        WHEAT_PRICE_PER_KG    = 1.5

        gold_val   = gold_grams   * GOLD_PRICE_PER_GRAM
        silver_val = silver_grams * SILVER_PRICE_PER_GRAM
        crops_val  = crops_kg     * WHEAT_PRICE_PER_KG
        crop_rate  = 0.05 if irrigated.strip() in ("ن", "y") else 0.10

        results: List[Dict] = []

        def _check(label: str, value: float, rate: float, nisab: float) -> None:
            z = value * rate if value >= nisab else 0.0
            results.append({"label": label, "value": value, "nisab": nisab,
                            "rate": rate, "zakat": z,
                            "eligible": value >= nisab})

        _check("النقود والأرصدة",   cash,        ZAKAT_RATE, NISAB_SAR)
        _check("عروض التجارة",      trade_goods, ZAKAT_RATE, NISAB_SAR)
        _check("الذهب",             gold_val,    ZAKAT_RATE, 85 * GOLD_PRICE_PER_GRAM)
        _check("الفضة",             silver_val,  ZAKAT_RATE, 595 * SILVER_PRICE_PER_GRAM)
        _check("الزراعة",           crops_val,   crop_rate,  653 * WHEAT_PRICE_PER_KG)

        camel_z = 0.0
        if camels >= 5:
            camel_z = (camels // 5) * (0.025 * NISAB_SAR)
        results.append({"label": "الإبل", "value": camels, "nisab": 5,
                        "rate": 0, "zakat": camel_z, "eligible": camels >= 5})

        cattle_z = 0.0
        if cattle >= 30:
            cattle_z = (cattle // 30) * (0.025 * NISAB_SAR)
        results.append({"label": "البقر", "value": cattle, "nisab": 30,
                        "rate": 0, "zakat": cattle_z, "eligible": cattle >= 30})

        sheep_z = 0.0
        if sheep >= 40:
            sheep_z = (sheep // 40) * (0.025 * NISAB_SAR)
        results.append({"label": "الغنم", "value": sheep, "nisab": 40,
                        "rate": 0, "zakat": sheep_z, "eligible": sheep >= 40})

        Printer.divider()
        Printer.header("📋 نتيجة حاسبة الزكاة")
        total_zakat = 0.0
        for r in results:
            if r["value"] == 0:
                continue
            clr  = Colors.GREEN if r["eligible"] else Colors.RED
            mark = "✓ واجبة" if r["eligible"] else "✗ دون النصاب"
            rate_str = f"{r['rate']*100:.1f}%" if r["rate"] else "—"
            print(
                f"  {clr}{mark}{Colors.RESET}  "
                f"{Colors.CYAN}{r['label']:<22}{Colors.RESET}  "
                f"القيمة: {r['value']:>12,.2f}  "
                f"النسبة: {rate_str}  "
                f"{Colors.BOLD}الزكاة: {r['zakat']:>10,.2f} ريال{Colors.RESET}"
            )
            total_zakat += r["zakat"]

        Printer.divider()
        clr = Colors.GREEN if total_zakat > 0 else Colors.YELLOW
        print(f"\n  {Colors.BOLD}إجمالي الزكاة الواجبة: {clr}{total_zakat:,.2f} ريال{Colors.RESET}\n")

        if total_zakat > 0:
            Printer.section("مصارف الزكاة الثمانية")
            share = total_zakat / 8
            for cat in ZakatCategory:
                print(f"  {Colors.GREEN}▸{Colors.RESET}  {cat.value:<30}  "
                      f"{Colors.DIM}الحصة: {share:,.2f} ريال{Colors.RESET}")

            Printer.divider()
            record = self._prompt("تسجيل هذه الزكاة تبرعاً في المنظومة؟ (ن/ل)", "ن")
            if record.strip() in ("ن", "y"):
                name  = self._prompt("اسمك")
                phone = self._prompt("هاتفك")
                ok, msg = self.eco.finance.receive_donation(
                    name, phone, total_zakat, FundType.ZAKAT, "ZAKAT-CALC"
                )
                (Printer.success if ok else Printer.error)(msg)

    def _show_statistics_dashboard(self) -> None:
        """
        لوحة الإحصاء الشاملة بمخططات ASCII.

        تعرض: توزيع حالات الطلبات، مقارنة إنفاق القطاعات،
        توزيع الأرصدة، ومستوى نشاط كل قطاع.
        """
        Printer.header("📊 لوحة الإحصاء والمخططات")
        print(f"  {Colors.YELLOW}📅  {HijriCalendar.today_dual()}{Colors.RESET}\n")
        BAR = 32

        def _bar(val: float, max_val: float, width: int = BAR) -> str:
            filled = int((val / max_val) * width) if max_val > 0 else 0
            return (f"{Colors.CYAN}{'█' * filled}"
                    f"{Colors.DIM}{'░' * (width - filled)}{Colors.RESET}")

        # ── توزيع حالات الطلبات ─────────────────────────────────────────
        Printer.section("توزيع حالات الطلبات")
        status_counts: Dict[str, int] = {}
        for a in self.eco._all_applications.values():
            status_counts[a.status.value] = status_counts.get(a.status.value, 0) + 1
        max_sc = max(status_counts.values(), default=1)
        for status_val, count in sorted(status_counts.items(),
                                        key=lambda x: x[1], reverse=True):
            print(f"  {Colors.YELLOW}{status_val:<26}{Colors.RESET} "
                  f"{_bar(count, max_sc)}  {Colors.BOLD}{count:>4}{Colors.RESET}")

        # ── مقارنة إنفاق القطاعات ────────────────────────────────────────
        Printer.section("إجمالي الإنفاق بالقطاعات (ريال)")
        sector_spend: Dict[str, float] = {}
        for a in self.eco._all_applications.values():
            if a.approved_amount > 0 and a.status in (
                ApplicationStatus.APPROVED, ApplicationStatus.DISBURSED
            ):
                sector_spend[a.sector.value] = (
                    sector_spend.get(a.sector.value, 0.0) + a.approved_amount
                )
        max_sp = max(sector_spend.values(), default=1.0)
        for sec, amt in sorted(sector_spend.items(), key=lambda x: x[1], reverse=True):
            print(f"  {Colors.GREEN}{sec:<26}{Colors.RESET} "
                  f"{_bar(amt, max_sp, BAR)}  "
                  f"{Colors.BOLD}{amt:>12,.0f}{Colors.RESET}")
        if not sector_spend:
            Printer.info("لا توجد مدفوعات بعد")

        # ── توزيع الأرصدة على الصناديق ──────────────────────────────────
        Printer.section("توزيع الأرصدة على الصناديق الأربعة")
        balances = {ft: self.eco.finance.get_balance(ft) for ft in FundType}
        total_bal = sum(balances.values()) or 1.0
        for ft, bal in balances.items():
            pct = (bal / total_bal) * 100
            print(f"  {Colors.MAGENTA}{ft.value:<26}{Colors.RESET} "
                  f"{_bar(bal, total_bal)}  "
                  f"{Colors.BOLD}{bal:>12,.0f}  {pct:5.1f}%{Colors.RESET}")

        # ── مؤشر نشاط المستفيدين ────────────────────────────────────────
        Printer.section("نشاط المستفيدين (عدد الطلبات لكل مستفيد)")
        ben_activity: Dict[str, int] = {}
        for a in self.eco._all_applications.values():
            ben_activity[a.beneficiary_id] = ben_activity.get(a.beneficiary_id, 0) + 1
        max_act = max(ben_activity.values(), default=1)
        sorted_bens = sorted(ben_activity.items(), key=lambda x: x[1], reverse=True)[:8]
        for ben_id, count in sorted_bens:
            ben = self.eco._beneficiaries.get(ben_id)
            name = ben.full_name if ben else ben_id
            print(f"  {Colors.CYAN}{name:<26}{Colors.RESET} "
                  f"{_bar(count, max_act, 20)}  "
                  f"{Colors.BOLD}{count} طلب{Colors.RESET}")

        # ── ملخص أرقام فورية ────────────────────────────────────────────
        Printer.divider()
        fin = self.eco.finance.get_financial_report()
        total_b = len(self.eco._beneficiaries)
        elig_b  = sum(1 for b in self.eco._beneficiaries.values() if b.is_eligible)
        total_a = len(self.eco._all_applications)
        appr_a  = sum(1 for a in self.eco._all_applications.values()
                      if a.status in (ApplicationStatus.APPROVED,
                                      ApplicationStatus.DISBURSED))
        print(f"\n  {'المستفيدون':<22} {Colors.BOLD}{total_b}{Colors.RESET} "
              f"(مؤهلون: {Colors.GREEN}{elig_b}{Colors.RESET})")
        print(f"  {'الطلبات':<22} {Colors.BOLD}{total_a}{Colors.RESET} "
              f"(معتمدة/مصروفة: {Colors.GREEN}{appr_a}{Colors.RESET})")
        print(f"  {'إجمالي التبرعات':<22} "
              f"{Colors.BOLD}{fin['total_received']:,.0f} ريال{Colors.RESET}")
        print(f"  {'إجمالي الصرف':<22} "
              f"{Colors.BOLD}{fin['total_disbursed']:,.0f} ريال{Colors.RESET}")
        eff = (fin['total_disbursed'] / fin['total_received'] * 100
               if fin['total_received'] else 0)
        print(f"  {'كفاءة الصرف':<22} "
              f"{Colors.BOLD}{Colors.GREEN}{eff:.1f}%{Colors.RESET}")

    def _search_interactive(self) -> None:
        """
        واجهة بحث موحّدة عن مستفيد أو طلب بأي حقل.

        تدعم البحث بالاسم أو رقم الهوية أو المعرّف أو الوصف.
        """
        Printer.header("🔍 بحث عن مستفيد أو طلب")
        query = self._prompt("أدخل نص البحث (اسم / هوية / معرّف / وصف)").strip()
        if not query:
            Printer.warning("لم تُدخل نصاً للبحث")
            return
        pat = re.compile(re.escape(query), re.IGNORECASE)

        found_b = [
            b for b in self.eco._beneficiaries.values()
            if pat.search(b.full_name)
            or pat.search(b.national_id)
            or pat.search(b.beneficiary_id)
            or pat.search(str(b.address))
        ]
        found_a = [
            a for a in self.eco._all_applications.values()
            if pat.search(a.application_id)
            or pat.search(a.beneficiary_id)
            or pat.search(a.description)
        ]

        if found_b:
            Printer.section(f"المستفيدون ({len(found_b)} نتيجة)")
            for b in found_b:
                elig_clr = Colors.GREEN if b.is_eligible else Colors.RED
                print(
                    f"  {Colors.CYAN}{b.beneficiary_id}{Colors.RESET}  "
                    f"{b.full_name:<22}  "
                    f"هوية: {b.national_id:<12}  "
                    f"{elig_clr}{'مؤهل' if b.is_eligible else 'غير مؤهل'}{Colors.RESET}  "
                    f"{Colors.DIM}{str(b.address)}{Colors.RESET}"
                )
        else:
            Printer.info("لا توجد مستفيدون مطابقون")

        if found_a:
            Printer.section(f"الطلبات ({len(found_a)} نتيجة)")
            for a in found_a:
                print(
                    f"  {Colors.CYAN}{a.application_id}{Colors.RESET}  "
                    f"{a.sector.value:<18}  "
                    f"{a.status.value:<22}  "
                    f"{Colors.BOLD}{a.requested_amount:>10,.0f} ريال{Colors.RESET}  "
                    f"{Colors.DIM}{a.description[:35]}...{Colors.RESET}"
                )
        else:
            Printer.info("لا توجد طلبات مطابقة")

    def _save_data_interactive(self) -> None:
        """
        حفظ بيانات المنظومة يدوياً إلى ملف JSON.

        يعرض موقع الملف المحفوظ بعد اكتمال العملية.
        """
        Printer.header("💾 حفظ البيانات")
        Printer.info("جارٍ حفظ البيانات...")
        ok, msg = self.persistence.save(self.eco)
        (Printer.success if ok else Printer.error)(msg)
        if ok:
            stats = (
                f"المستفيدون: {len(self.eco._beneficiaries)}  |  "
                f"الطلبات: {len(self.eco._all_applications)}  |  "
                f"العمليات: {len(self.eco.finance._transactions)}"
            )
            Printer.kv("إحصائيات المحفوظ", stats)

    def _export_report_interactive(self) -> None:
        """
        تصدير تقرير نصي شامل للمنظومة إلى ملف .txt.

        يتضمن التقرير: معلومات المنظومة، الأرصدة، مؤشرات القطاعات،
        قائمة المستفيدين، وملخص آخر العمليات المالية.
        """
        Printer.header("📤 تصدير تقرير شامل")
        default_name = f"charity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_name = self._prompt("اسم الملف", default_name)

        lines: List[str] = []
        sep  = "═" * 74
        thin = "─" * 74

        def ln(text: str = "") -> None:
            lines.append(text)

        # ── الترويسة ────────────────────────────────────────────────────
        ln(sep)
        ln(f"  منظومة العمل الخيري الذكي — تقرير شامل")
        ln(f"  تاريخ الإصدار: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        ln(sep)
        ln()

        # ── ملخص المنظومة ───────────────────────────────────────────────
        report = self.eco.get_ecosystem_report()
        ln("[ ملخص المنظومة ]")
        ln(thin)
        ln(f"  إجمالي المستفيدين    : {report['total_beneficiaries']}")
        ln(f"  المستفيدون المؤهلون  : {report['eligible_beneficiaries']}")
        ln(f"  إجمالي الطلبات       : {report['total_applications']}")
        ln()

        # ── التقرير المالي ──────────────────────────────────────────────
        fin = self.eco.finance.get_financial_report()
        ln("[ التقرير المالي ]")
        ln(thin)
        for fund_name, balance in fin["balances"].items():
            ln(f"  {fund_name:<25} : {balance:>14,.2f} ريال")
        ln(thin)
        ln(f"  إجمالي المستلم       : {fin['total_received']:>14,.2f} ريال")
        ln(f"  إجمالي المصروف       : {fin['total_disbursed']:>14,.2f} ريال")
        ln(f"  الرصيد الصافي        : {fin['total_received'] - fin['total_disbursed']:>14,.2f} ريال")
        ln(f"  عدد المتبرعين        : {fin['total_donors']}")
        ln()

        # ── مؤشرات القطاعات ─────────────────────────────────────────────
        ln("[ مؤشرات الأداء — القطاعات الأربعة ]")
        ln(thin)
        for sector_type, sector in self.eco.sectors.items():
            kpi = sector.generate_kpi_report()
            ln(f"  ▸ {sector_type.value}")
            ln(f"    الطلبات: {kpi.total_applications}  |  "
               f"المعتمدة: {kpi.approved_applications}  |  "
               f"المرفوضة: {kpi.rejected_applications}  |  "
               f"المصروف: {kpi.total_disbursed:,.0f} ريال  |  "
               f"نسبة الاعتماد: {kpi.approval_rate:.1f}%")
        ln()

        # ── قائمة المستفيدين ────────────────────────────────────────────
        ln("[ المستفيدون المسجّلون ]")
        ln(thin)
        for b in self.eco._beneficiaries.values():
            elig = "مؤهل  " if b.is_eligible else "غير مؤهل"
            ln(f"  {b.beneficiary_id}  {b.full_name:<22}  "
               f"{elig}  دخل: {b.monthly_income:,.0f} ريال/شهر  "
               f"أفراد: {b.family_size}")
        ln()

        # ── آخر العمليات ────────────────────────────────────────────────
        ln("[ آخر 10 عمليات مالية ]")
        ln(thin)
        for txn in self.eco.finance.get_transactions(limit=10):
            arrow = "▲ إيداع" if txn.transaction_type == "CREDIT" else "▼ صرف  "
            ln(f"  {str(txn.timestamp)[:19]}  {arrow}  "
               f"{txn.fund_type.value:<15}  "
               f"{txn.amount:>12,.2f} ريال  "
               f"{txn.description}")
        ln()
        ln(sep)
        ln("  نهاية التقرير")
        ln(sep)

        base = os.path.dirname(os.path.abspath(
            globals().get("__file__", os.getcwd())
        ))
        path = os.path.join(base, file_name)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines))
            Printer.success(f"تم التصدير بنجاح: {path}")
            Printer.kv("حجم الملف", f"{os.path.getsize(path):,} بايت")
        except Exception as exc:
            Printer.error(f"فشل التصدير: {exc}")

    # ══════════════════════════════════════════════════════════════════════
    #  التقارير والمتابعة
    # ══════════════════════════════════════════════════════════════════════

    def _show_predictions(self) -> None:
        """
        عرض تنبؤات الذكاء الاصطناعي بالاحتياجات المستقبلية.

        يحلل البيانات التاريخية ويعرض توقعات الشهر القادم
        لكل قطاع مع مؤشر شريطي ASCII.
        """
        Printer.header("🔮 التنبؤ بالاحتياجات المستقبلية")
        all_apps = list(self.eco._all_applications.values())
        predictions = self.eco.ai.predict_future_needs(all_apps)
        max_val = max(predictions.values()) if any(predictions.values()) else 1.0

        Printer.section("التوقعات المالية للشهر القادم (معامل نمو 10%)")
        bar_width = 30
        for sector, amount in predictions.items():
            filled = int((amount / max_val) * bar_width) if max_val > 0 else 0
            bar    = f"{Colors.GREEN}{'█' * filled}{Colors.DIM}{'░' * (bar_width - filled)}{Colors.RESET}"
            print(
                f"  {Colors.CYAN}{sector.value:<25}{Colors.RESET} "
                f"{bar} {Colors.BOLD}{amount:>10,.0f} ريال{Colors.RESET}"
            )

        Printer.divider()
        total = sum(predictions.values())
        Printer.kv("الإجمالي المتوقع", f"{total:,.2f} ريال")

        Printer.section("الأرصدة المتاحة الآن")
        fin_report = self.eco.finance.get_financial_report()
        for fund_name, balance in fin_report["balances"].items():
            clr = Colors.GREEN if balance >= total / len(FundType) else Colors.YELLOW
            print(f"  {Colors.CYAN}{fund_name:<25}{Colors.RESET} {clr}{balance:>12,.2f} ريال{Colors.RESET}")

    def _show_ecosystem_report(self) -> None:
        """عرض التقرير الشامل للمنظومة."""
        report = self.eco.get_ecosystem_report()
        Printer.header("📊 التقرير الشامل للمنظومة")

        Printer.section("معلومات المنظومة")
        Printer.kv("الاسم",                 report["organization"])
        Printer.kv("الإصدار",               report["version"])
        Printer.kv("تاريخ التقرير",          HijriCalendar.today_dual())
        Printer.kv("إجمالي المستفيدين",     report["total_beneficiaries"])
        Printer.kv("المستفيدون المؤهلون",   report["eligible_beneficiaries"])
        Printer.kv("إجمالي الطلبات",        report["total_applications"])

        Printer.section("مؤشرات الأداء — القطاعات الأربعة")
        for sector_name, kpi in report["sector_kpis"].items():
            print(f"\n  {Colors.BLUE}{Colors.BOLD}▸ {sector_name}{Colors.RESET}")
            Printer.kv("    إجمالي الطلبات",  kpi["total_applications"])
            Printer.kv("    المعتمدة",         kpi["approved_applications"])
            Printer.kv("    المرفوضة",         kpi["rejected_applications"])
            Printer.kv("    المصروف",          f"{kpi['total_disbursed']:,.2f} ريال")
            Printer.kv("    نسبة الاعتماد",    f"{kpi['approval_rate']:.1f}%")
            Printer.kv("    المستفيدون الفعليون", kpi["beneficiaries_served"])

    def _show_financial_report(self) -> None:
        """عرض التقرير المالي الكامل."""
        report = self.eco.finance.get_financial_report()
        Printer.header("💰 التقرير المالي التفصيلي")

        Printer.section("أرصدة الحسابات المنفصلة")
        for fund_name, balance in report["balances"].items():
            clr = Colors.GREEN if balance > 0 else Colors.RED
            print(
                f"  {Colors.CYAN}{fund_name:<25}{Colors.RESET}"
                f" {clr}{balance:>15,.2f} ريال{Colors.RESET}"
            )

        Printer.divider()
        Printer.kv("إجمالي المستلم",          f"{report['total_received']:,.2f} ريال")
        Printer.kv("إجمالي المصروف",          f"{report['total_disbursed']:,.2f} ريال")
        net = report["total_received"] - report["total_disbursed"]
        Printer.kv("الرصيد الإجمالي الصافي",  f"{net:,.2f} ريال")
        Printer.kv("عدد العمليات",             report["total_transactions"])
        Printer.kv("عدد المتبرعين",            report["total_donors"])

        Printer.section("آخر العمليات المالية")
        for txn in self.eco.finance.get_transactions(limit=5):
            arrow = f"{Colors.GREEN}▲{Colors.RESET}" if txn.transaction_type == "CREDIT" else f"{Colors.RED}▼{Colors.RESET}"
            print(
                f"  {arrow} {txn.transaction_id:<18} "
                f"{txn.fund_type.value:<15} "
                f"{Colors.BOLD}{txn.amount:>12,.2f} ريال{Colors.RESET}  "
                f"{Colors.DIM}{txn.description}{Colors.RESET}"
            )

    def _show_sector(self, sector_type: SectorType) -> None:
        """عرض تقرير قطاع تشغيلي."""
        sector = self.eco.sectors[sector_type]
        kpi    = sector.generate_kpi_report()
        info   = sector.get_sector_specific_info()

        Printer.header(f"قطاع {sector_type.value}")
        Printer.section("مؤشرات الأداء الرئيسية")
        Printer.kv("إجمالي الطلبات",        kpi.total_applications)
        Printer.kv("المعتمدة",               kpi.approved_applications)
        Printer.kv("المرفوضة",               kpi.rejected_applications)
        Printer.kv("إجمالي المصروف",        f"{kpi.total_disbursed:,.2f} ريال")
        Printer.kv("نسبة الاعتماد",          f"{kpi.approval_rate:.1f}%")
        Printer.kv("المستفيدون الفعليون",   kpi.beneficiaries_served)

        Printer.section("إحصائيات خاصة بالقطاع")
        for key, val in info.items():
            if key != "sector":
                Printer.kv(key, val)

        Printer.section("قائمة الطلبات")
        apps = sector.get_applications()
        if not apps:
            Printer.info("لا توجد طلبات حتى الآن")
            return
        for app in apps:
            priority_clr = (
                Colors.RED    if app.priority == Priority.CRITICAL else
                Colors.YELLOW if app.priority == Priority.HIGH     else
                Colors.WHITE
            )
            print(
                f"  {Colors.CYAN}{app.application_id}{Colors.RESET}  "
                f"{priority_clr}{app.priority.name:<8}{Colors.RESET}  "
                f"{app.status.value:<20}  "
                f"{Colors.BOLD}{app.requested_amount:>10,.0f} ريال{Colors.RESET}"
            )

    def _show_audit_log(self) -> None:
        """عرض سجل التدقيق والحوكمة."""
        Printer.header("🛡️ سجل التدقيق والحوكمة")
        print(f"  {Colors.YELLOW}📅  {HijriCalendar.today_dual()}{Colors.RESET}\n")
        logs = self.eco.governance.get_audit_log()
        if not logs:
            Printer.info("لا توجد سجلات حتى الآن")
            return
        for entry in logs:
            Printer.divider()
            Printer.kv("الوقت",      entry["timestamp"])
            Printer.kv("الإجراء",   entry["action"])
            Printer.kv("المنفّذ",   entry["actor"])
            Printer.kv("التفاصيل", entry["details"])

    def _show_ai_summary(self) -> None:
        """عرض ملخص أداء الذكاء الاصطناعي."""
        Printer.header("🧠 ملخص نواة الذكاء الاصطناعي")
        summary = self.eco.ai.get_experience_summary()

        Printer.section("إحصائيات التحليل")
        Printer.kv("إجمالي الحالات المحللة",   summary.get("total_analyzed", 0))
        if summary.get("total_analyzed", 0) > 0:
            Printer.kv("متوسط نقاط التقييم",    f"{summary.get('average_score', 0):.1f} / 100")
            Printer.kv("حالات الأولوية العالية", summary.get("high_priority_count", 0))

        Printer.section("الضوابط الشرعية المُطبّقة")
        Printer.kv("حد النصاب",                    f"{SmartAI.NISAB_THRESHOLD:,.2f} ريال")
        Printer.kv("الحد الأقصى لنصيب الفرد",     f"{SmartAI.MAX_ELIGIBLE_INCOME_PER_CAPITA:,.2f} ريال/شهر")
        Printer.kv("الحد الأقصى للصرف من الزكاة", f"{SmartAI.MAX_ZAKAT_PER_APPLICATION:,.2f} ريال")

        Printer.section("مصارف الزكاة الثمانية")
        for cat in ZakatCategory:
            print(f"  {Colors.GREEN}✓{Colors.RESET}  {cat.value}")

    def _show_policies(self) -> None:
        """عرض السياسات والإجراءات المعتمدة."""
        Printer.header("📋 السياسات والإجراءات المعتمدة")
        for policy in self.eco.governance.get_policies():
            Printer.divider()
            Printer.kv("الرمز",    policy["code"])
            Printer.kv("العنوان", policy["title"])
            Printer.kv("الوصف",  policy["description"])

    @staticmethod
    def _farewell() -> None:
        """طباعة رسالة الوداع."""
        print(f"\n{Colors.GREEN}{Colors.BOLD}")
        print("  ╔════════════════════════════════════════╗")
        print("  ║   شكراً لاستخدامك منظومة العمل الخيري ║")
        print("  ║      جعله الله في ميزان حسناتكم       ║")
        print("  ╚════════════════════════════════════════╝")
        print(Colors.RESET)


# ═══════════════════════════════════════════════════════════════════════════════
#  نقطة الدخول الرئيسية
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """
    نقطة الدخول الرئيسية لتشغيل المنظومة.

    تُهيّئ SmartCharityEcosystem وتشغّل واجهة CLI التفاعلية.
    """
    try:
        ecosystem = SmartCharityEcosystem()
        cli = CLI(ecosystem)
        cli.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}  تم إيقاف البرنامج بواسطة المستخدم.{Colors.RESET}\n")
        sys.exit(0)
    except Exception as exc:
        logging.getLogger("main").critical(
            "خطأ غير متوقع: %s", exc, exc_info=True
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
