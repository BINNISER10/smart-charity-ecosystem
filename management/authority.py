"""
مصفوفة الصلاحيات والتوكيل — Authority Matrix & Delegation
==========================================================
يُحدّد:
  - حدود الموافقة لكل دور (Approval Limits)
  - التوكيل المؤقت للصلاحيات (Delegation)
  - التحقق من صلاحية الموافقة (can_approve)

مصفوفة حدود الموافقة (بالريال السعودي):
  ┌──────────────────┬───────────────┐
  │ SYSTEM_ADMIN     │  غير محدود   │
  │ EXECUTIVE_DIR    │  500,000 ريال │
  │ FINANCE_MGR      │  100,000 ريال │
  │ SECTOR_MGR       │   50,000 ريال │
  │ CASE_WORKER      │   10,000 ريال │
  │ AUDITOR          │       0 ريال  │
  └──────────────────┴───────────────┘

مبدأ التوكيل:
  - لا يمكن توكيل صلاحيات أعلى مما يملكه الموكِّل
  - التوكيل مؤقت ومقيّد بتاريخ انتهاء
  - كل توكيل يُسجَّل في سجل التدقيق
"""

from __future__ import annotations
from typing import Dict, Optional
from smart_charity_ecosystem import GovernanceSystem, UserRole


# حدود الموافقة المالية لكل دور
APPROVAL_LIMITS: Dict[str, float] = {
    UserRole.SYSTEM_ADMIN.value:  float("inf"),
    UserRole.EXECUTIVE_DIR.value: 500_000.0,
    UserRole.FINANCE_MGR.value:   100_000.0,
    UserRole.SECTOR_MGR.value:     50_000.0,
    UserRole.CASE_WORKER.value:    10_000.0,
    UserRole.AUDITOR.value:             0.0,
}


class ApprovalMatrix:
    """
    مصفوفة الصلاحيات — واجهة للاستعلام عن حدود الموافقة.

    الاستخدام::

        matrix = ApprovalMatrix(governance)
        limit  = matrix.get_limit("USER-001")
        ok     = matrix.can_approve("USER-001", 25_000)
    """

    def __init__(self, governance: GovernanceSystem) -> None:
        self._gov = governance

    def get_limit(self, user_id: str) -> float:
        """إرجاع الحد المالي الأقصى للمستخدم."""
        user = self._gov._users.get(user_id)
        if not user:
            return 0.0
        role = user["role"]
        role_val = role.value if hasattr(role, "value") else str(role)
        return APPROVAL_LIMITS.get(role_val, 0.0)

    def can_approve(self, user_id: str, amount: float) -> bool:
        """التحقق من صلاحية الموافقة على مبلغ محدد."""
        return self.get_limit(user_id) >= amount

    def get_matrix_summary(self) -> Dict[str, str]:
        """ملخص مصفوفة الصلاحيات لجميع الأدوار."""
        return {
            role: f"{limit:,.0f} ريال" if limit != float("inf") else "غير محدود"
            for role, limit in APPROVAL_LIMITS.items()
        }


__all__ = ["ApprovalMatrix", "APPROVAL_LIMITS"]
