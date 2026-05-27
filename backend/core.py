#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tenant Registry — core.py
سجل المنظومات المعزولة لكل مستأجر (Lazy-initialized per-tenant ecosystem).
كل مستأجر يحصل على نسخة SmartCharityEcosystem مستقلة تماماً.
"""
from __future__ import annotations

import os
import sys
import logging
from typing import Dict

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from smart_charity_ecosystem import SmartCharityEcosystem, DataPersistence

logger = logging.getLogger("core.tenant_registry")

# ── سجل المنظومات {tenant_id: eco} ──────────────────────────────────────────
_registry: Dict[str, SmartCharityEcosystem] = {}


def get_eco(tenant_id: str) -> SmartCharityEcosystem:
    """
    إرجاع (أو إنشاء) نسخة SmartCharityEcosystem للمستأجر المحدد.
    يُحمَّل ملف الحفظ الخاص بالمستأجر عند الإنشاء الأول.
    """
    if tenant_id not in _registry:
        eco = SmartCharityEcosystem()
        persistence = DataPersistence(tenant_id=tenant_id)
        ok, msg = persistence.load(eco)
        if ok:
            logger.info("تم تحميل بيانات المستأجر '%s': %s", tenant_id, msg)
        else:
            logger.info("مستأجر جديد '%s' — جلسة فارغة", tenant_id)
        _registry[tenant_id] = eco

    return _registry[tenant_id]


def save_eco(tenant_id: str) -> tuple[bool, str]:
    """حفظ حالة المنظومة للمستأجر المحدد."""
    eco = _registry.get(tenant_id)
    if not eco:
        return False, f"المستأجر '{tenant_id}' غير محمّل في السجل"
    persistence = DataPersistence(tenant_id=tenant_id)
    return persistence.save(eco)


def evict_eco(tenant_id: str) -> None:
    """إزالة نسخة المستأجر من الذاكرة (للاختبارات أو إعادة التحميل)."""
    _registry.pop(tenant_id, None)
    logger.debug("تمت إزالة المستأجر '%s' من السجل", tenant_id)
