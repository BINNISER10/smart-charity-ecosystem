#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase Persistence Layer — supabase_client.py

يوفر SupabasePersistence كبديل لـ DataPersistence المعتمدة على JSON،
مع عزل تام لبيانات كل مستأجر عبر فلترة tenant_id في كل استعلام.

يستلزم متغيرات البيئة:
    SUPABASE_URL          — رابط مشروع Supabase
    SUPABASE_SERVICE_KEY  — مفتاح الخدمة (Service Role Key)

يتراجع تلقائياً إلى DataPersistence (JSON) إذا لم تُوجد هذه المتغيرات
أو إذا لم تُثبَّت مكتبة supabase-py.
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any, Dict, Optional, Tuple

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from smart_charity_ecosystem import (
    ApplicationStatus, DataPersistence, FundType, SectorType,
    SmartCharityEcosystem, ZakatCategory,
)

logger = logging.getLogger("supabase_persistence")

# ── محاولة استيراد مكتبة supabase-py ────────────────────────────────────────
try:
    from supabase import create_client, Client as SupabaseClient  # type: ignore
    _SUPABASE_LIB = True
except ImportError:
    _SUPABASE_LIB = False
    logger.warning(
        "مكتبة supabase-py غير مثبتة — جاري الرجوع إلى JSON. "
        "قم بتثبيتها عبر: pip install supabase"
    )

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")


def _get_client() -> Optional["SupabaseClient"]:
    """إرجاع عميل Supabase إذا توفرت المتغيرات والمكتبة، وإلا None."""
    if not _SUPABASE_LIB:
        return None
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.debug("SUPABASE_URL/SUPABASE_SERVICE_KEY غير مضبوطة")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


class SupabasePersistence(DataPersistence):
    """
    طبقة استمرارية تعتمد Supabase كقاعدة بيانات مع عزل تام للمستأجرين.

    تُضمن كل عملية SELECT/INSERT/UPDATE/UPSERT فلترة tenant_id
    لمنع أي تسرب بيانات بين الجمعيات.

    عند غياب الاتصال أو المكتبة، يتراجع الكود للحفظ في ملف JSON.
    """

    TABLES = {
        "beneficiaries": "beneficiaries",
        "applications":  "applications",
        "transactions":  "transactions",
        "donors":        "donors",
    }

    def __init__(self, tenant_id: str = "default") -> None:
        super().__init__(tenant_id=tenant_id)
        self._client = _get_client()
        self._use_supabase = self._client is not None
        if self._use_supabase:
            logger.info(
                "Supabase متاح — المستأجر '%s' يُخزَّن في السحابة", tenant_id
            )

    # ── العمليات العلنية ──────────────────────────────────────────────────────

    def save(self, eco: SmartCharityEcosystem) -> Tuple[bool, str]:
        if not self._use_supabase:
            return super().save(eco)
        try:
            return self._save_to_supabase(eco)
        except Exception as exc:
            logger.error("فشل الحفظ في Supabase: %s — جاري الرجوع لـ JSON", exc)
            return super().save(eco)

    def load(self, eco: SmartCharityEcosystem) -> Tuple[bool, str]:
        if not self._use_supabase:
            return super().load(eco)
        try:
            return self._load_from_supabase(eco)
        except Exception as exc:
            logger.error("فشل التحميل من Supabase: %s — جاري الرجوع لـ JSON", exc)
            return super().load(eco)

    # ── حفظ في Supabase ───────────────────────────────────────────────────────

    def _save_to_supabase(self, eco: SmartCharityEcosystem) -> Tuple[bool, str]:
        tid = self.tenant_id

        # المستفيدون
        for b in eco._beneficiaries.values():
            if b.tenant_id != tid:
                continue
            row = self._ben_to_dict(b)
            (self._client.table(self.TABLES["beneficiaries"])
             .upsert(row, on_conflict="beneficiary_id")
             .execute())

        # الطلبات
        for a in eco._all_applications.values():
            if a.tenant_id != tid:
                continue
            row = self._app_to_dict(a)
            (self._client.table(self.TABLES["applications"])
             .upsert(row, on_conflict="application_id")
             .execute())

        # المعاملات المالية
        for t in eco.finance._transactions:
            if t.tenant_id != tid:
                continue
            row = self._txn_to_dict(t)
            (self._client.table(self.TABLES["transactions"])
             .upsert(row, on_conflict="transaction_id")
             .execute())

        # الأرصدة (جدول مخصص للرصيد الإجمالي لكل مستأجر وصندوق)
        for ft, balance in eco.finance._balances.items():
            (self._client.table("fund_balances")
             .upsert({
                 "tenant_id": tid,
                 "fund_type": ft.value,
                 "balance":   balance,
             }, on_conflict="tenant_id,fund_type")
             .execute())

        return True, f"تم الحفظ في Supabase — المستأجر: {tid}"

    # ── تحميل من Supabase ─────────────────────────────────────────────────────

    def _load_from_supabase(self, eco: SmartCharityEcosystem) -> Tuple[bool, str]:
        tid = self.tenant_id

        # المستفيدون
        resp = (self._client.table(self.TABLES["beneficiaries"])
                .select("*")
                .eq("tenant_id", tid)
                .execute())
        for d in resp.data or []:
            b = self._dict_to_ben(d)
            eco._beneficiaries[b.beneficiary_id] = b

        # الطلبات
        resp = (self._client.table(self.TABLES["applications"])
                .select("*")
                .eq("tenant_id", tid)
                .execute())
        for d in resp.data or []:
            a = self._dict_to_app(d)
            eco._all_applications[a.application_id] = a
            if a.sector in eco.sectors:
                eco.sectors[a.sector]._applications.append(a)

        # المعاملات المالية
        resp = (self._client.table(self.TABLES["transactions"])
                .select("*")
                .eq("tenant_id", tid)
                .execute())
        eco.finance._transactions = [
            self._dict_to_txn(d) for d in (resp.data or [])
        ]

        # الأرصدة
        resp = (self._client.table("fund_balances")
                .select("*")
                .eq("tenant_id", tid)
                .execute())
        for row in resp.data or []:
            try:
                ft = FundType(row["fund_type"])
                eco.finance._balances[ft] = float(row["balance"])
            except (ValueError, KeyError):
                pass

        count_b = len(eco._beneficiaries)
        count_a = len(eco._all_applications)
        return True, f"تم التحميل من Supabase — {count_b} مستفيد، {count_a} طلب"
