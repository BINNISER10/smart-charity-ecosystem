"""
إدارة الصدقات والتبرعات — Donations Manager
============================================
يُدير:
  - تسجيل التبرعات النقدية وتوجيهها للصندوق المناسب
  - سجل المتبرعين وتاريخ تبرعاتهم
  - البحث في قائمة المتبرعين وتحديث بياناتهم

الصناديق الأربعة:
  ┌─────────────────────────────┬──────────────────────────────────────┐
  │ صندوق الزكاة                │ للمستحقين الشرعيين (8 أصناف)        │
  │ صندوق الصدقات العامة        │ للاحتياجات العامة والطارئة           │
  │ صندوق الكفالات والأوقاف     │ للمشاريع المستدامة والأوقاف          │
  │ صندوق الطوارئ والأزمات      │ للكوارث والأزمات الإنسانية الطارئة  │
  └─────────────────────────────┴──────────────────────────────────────┘
"""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from smart_charity_ecosystem import SmartCharityEcosystem

from smart_charity_ecosystem import FundType, DonorRecord


class DonationsManager:
    """
    مدير التبرعات — واجهة موحّدة لعمليات التبرع وإدارة المتبرعين.

    الاستخدام::

        dm = DonationsManager(eco)

        # تسجيل تبرع
        ok, msg = dm.receive("محمد العمري", "0501234567", 5000, "الزكاة")

        # البحث في المتبرعين
        donors = dm.search("محمد")

        # تقرير المتبرعين
        report = dm.get_donors_report()
    """

    def __init__(self, eco: "SmartCharityEcosystem") -> None:
        self._eco = eco

    def receive(
        self,
        donor_name:  str,
        donor_phone: str,
        amount:      float,
        fund_name:   str,
        executor_id: str = "SYSTEM",
    ) -> tuple[bool, str]:
        """
        تسجيل تبرع جديد.

        المعاملات:
            donor_name  : اسم المتبرع.
            donor_phone : هاتف المتبرع.
            amount      : القيمة بالريال.
            fund_name   : اسم الصندوق (قيمة FundType).
            executor_id : مُنفِّذ العملية.

        المخرجات:
            (success, message)
        """
        try:
            fund_type = FundType(fund_name)
        except ValueError:
            return False, f"صندوق غير معروف: {fund_name}"
        return self._eco.finance.receive_donation(
            donor_name, donor_phone, amount, fund_type, executor_id
        )

    def search(self, query: str) -> List[DonorRecord]:
        """البحث عن متبرع باسمه أو هاتفه."""
        q = query.lower()
        return [
            d for d in self._eco.finance._donors.values()
            if q in d.full_name.lower() or q in d.phone
        ]

    def all_donors(self) -> List[DonorRecord]:
        """قائمة جميع المتبرعين."""
        return list(self._eco.finance._donors.values())

    def get_donors_report(self) -> Dict[str, Any]:
        """تقرير شامل عن المتبرعين."""
        donors = self.all_donors()
        if not donors:
            return {"total": 0, "total_donated": 0.0, "top_donors": []}
        donors.sort(key=lambda d: d.total_donated, reverse=True)
        return {
            "total":        len(donors),
            "total_donated": sum(d.total_donated for d in donors),
            "avg_donation":  sum(d.total_donated for d in donors) / len(donors),
            "top_donors": [
                {
                    "name":         d.full_name,
                    "phone":        d.phone,
                    "fund_type":    d.fund_type.value,
                    "total":        d.total_donated,
                    "count":        d.donation_count,
                }
                for d in donors[:10]
            ],
        }

    def fund_balances(self) -> Dict[str, float]:
        """أرصدة الصناديق الأربعة."""
        return {
            ft.value: self._eco.finance._balances.get(ft, 0.0)
            for ft in FundType
        }


__all__ = ["DonationsManager"]
