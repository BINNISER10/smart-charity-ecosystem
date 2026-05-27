"""
نماذج البيانات المشتركة — Shared Data Models
=============================================
تحتوي على جميع الـ Enums والـ Dataclasses المستخدمة في المنظومة:
  - ZakatCategory   : فئات الزكاة الشرعية الثمان
  - FundType        : أنواع الصناديق المالية الأربعة
  - ApplicationStatus : حالات دورة حياة الطلب (9 حالات)
  - Priority        : مستويات الأولوية
  - UserRole        : أدوار المستخدمين وصلاحياتهم
  - SectorType      : القطاعات التشغيلية الأربعة
  - Address         : نموذج العنوان
  - Beneficiary     : نموذج المستفيد
  - Application     : نموذج الطلب
  - Transaction     : نموذج العملية المالية
  - DonorRecord     : نموذج المتبرع
  - KPIReport       : نموذج تقرير الأداء
"""

from smart_charity_ecosystem import (
    ZakatCategory,
    FundType,
    ApplicationStatus,
    Priority,
    UserRole,
    SectorType,
    Address,
    Beneficiary,
    Application,
    Transaction,
    DonorRecord,
    KPIReport,
)

__all__ = [
    "ZakatCategory",
    "FundType",
    "ApplicationStatus",
    "Priority",
    "UserRole",
    "SectorType",
    "Address",
    "Beneficiary",
    "Application",
    "Transaction",
    "DonorRecord",
    "KPIReport",
]
