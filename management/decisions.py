"""
نظام اتخاذ القرارات والتعميد — Decision Engine
================================================
يُدير:
  - دورة حياة الموافقة على الطلبات (موافقة / رفض / إلغاء)
  - سجل التدقيق (Audit Trail) لكل قرار
  - تعميد القرارات وتوثيقها رسمياً

دورة حياة القرار:
  SUBMITTED → [AI_ANALYZED] → PENDING_APPROVAL
    ↓ موافقة         ↓ رفض          ↓ إلغاء
  APPROVED        REJECTED       CANCELLED
    ↓ صرف
  DISBURSED
"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any

if TYPE_CHECKING:
    from smart_charity_ecosystem import SmartCharityEcosystem, Application

from smart_charity_ecosystem import GovernanceSystem, ApplicationStatus


class DecisionEngine:
    """
    محرك القرارات — يُغلّف عمليات الموافقة والرفض والإلغاء.

    الاستخدام::

        engine = DecisionEngine(eco)

        # موافقة
        ok, msg = engine.approve("APP-001", "USR-001", 5000, "موافق")

        # رفض
        engine.reject("APP-001", "USR-001", "لا يستوفي الشروط")

        # عرض سجل التدقيق
        log = engine.get_audit_log(limit=20)
    """

    def __init__(self, eco: "SmartCharityEcosystem") -> None:
        self._eco = eco

    # ── قرارات ──────────────────────────────────────────────────────────────

    def approve(
        self,
        application_id: str,
        approver_id: str,
        approved_amount: float,
        notes: str = "",
    ) -> tuple[bool, str]:
        """
        الموافقة الرسمية على طلب.

        المخرجات:
            (success, message)
        """
        return self._eco.process_approval(
            application_id, approver_id, approved_amount, notes
        )

    def reject(
        self,
        application_id: str,
        rejector_id: str,
        reason: str,
    ) -> tuple[bool, str]:
        """
        رفض طلب مع توثيق السبب.

        المخرجات:
            (success, message)
        """
        app = self._eco._all_applications.get(application_id)
        if not app:
            return False, f"الطلب {application_id} غير موجود"
        self._eco.governance.reject_application(app, rejector_id, reason)
        return True, f"تم رفض الطلب {application_id}"

    def cancel(
        self,
        application_id: str,
        canceller_id: str,
        reason: str = "",
    ) -> tuple[bool, str]:
        """
        إلغاء طلب.

        المخرجات:
            (success, message)
        """
        app = self._eco._all_applications.get(application_id)
        if not app:
            return False, f"الطلب {application_id} غير موجود"
        ok = self._eco.governance.cancel_application(app, canceller_id, reason)
        if ok:
            return True, f"تم إلغاء الطلب {application_id}"
        return False, "لا يمكن إلغاء الطلب بحالته الحالية"

    def disburse(
        self,
        application_id: str,
        executor_id: str,
    ) -> tuple[bool, str]:
        """
        صرف المبلغ المعتمد لطلب موافق عليه.

        المخرجات:
            (success, message)
        """
        return self._eco.process_disbursement(application_id, executor_id)

    # ── سجل التدقيق ─────────────────────────────────────────────────────────

    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """استرجاع سجل التدقيق."""
        return self._eco.governance.get_audit_log(limit)

    def get_application_history(self, application_id: str) -> List[Dict[str, Any]]:
        """سجل تدقيق طلب محدد."""
        app = self._eco._all_applications.get(application_id)
        if not app:
            return []
        return app.audit_trail

    # ── إحصاءات ──────────────────────────────────────────────────────────────

    def pending_count(self) -> int:
        """عدد الطلبات بانتظار القرار."""
        pending = (
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.AI_ANALYZED,
            ApplicationStatus.PENDING_APPROVAL,
        )
        return sum(
            1 for a in self._eco._all_applications.values()
            if a.status in pending
        )


__all__ = ["DecisionEngine"]
