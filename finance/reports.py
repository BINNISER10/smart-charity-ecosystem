"""
التقارير المالية والشرعية — Financial & Sharia Reports
=======================================================
يُنتج:
  - التقرير المالي الشامل (أرصدة + إجماليات)
  - سجل المعاملات مع فلترة متقدمة
  - تقرير كفاءة الصرف
  - ملخص الزكاة المحصَّلة والمُوزَّعة
  - تقرير مؤشرات الأداء (KPI) لكل صندوق
"""

from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from smart_charity_ecosystem import SmartCharityEcosystem

from smart_charity_ecosystem import FundType, Transaction


class FinanceReporter:
    """
    مولّد التقارير المالية.

    الاستخدام::

        reporter = FinanceReporter(eco)

        # تقرير شامل
        full = reporter.full_report()

        # معاملات آخر 30 يوم
        txns = reporter.transactions(limit=30)

        # كفاءة الصرف
        eff = reporter.disbursement_efficiency()
    """

    def __init__(self, eco: "SmartCharityEcosystem") -> None:
        self._eco = eco

    # ── التقارير الرئيسية ───────────────────────────────────────────────────

    def full_report(self) -> Dict[str, Any]:
        """التقرير المالي الشامل."""
        return self._eco.finance.get_financial_report()

    def transactions(
        self,
        fund_type:  Optional[str] = None,
        limit:      int           = 50,
        from_date:  Optional[date] = None,
        to_date:    Optional[date] = None,
    ) -> List[Transaction]:
        """
        استرجاع المعاملات مع الفلترة.

        المعاملات:
            fund_type : فلتر نوع الصندوق (اختياري).
            limit     : الحد الأقصى للنتائج.
            from_date : تاريخ البداية (اختياري).
            to_date   : تاريخ النهاية (اختياري).
        """
        ft = FundType(fund_type) if fund_type else None
        return self._eco.finance.get_transactions(ft, limit, from_date, to_date)

    def disbursement_efficiency(self) -> Dict[str, Any]:
        """
        مؤشر كفاءة الصرف: نسبة ما وصل للمستفيدين من إجمالي التبرعات.
        """
        report       = self.full_report()
        total_in     = report.get("total_received",   0.0)
        total_out    = report.get("total_disbursed",  0.0)
        total_ops    = report.get("total_expenses",   0.0)
        efficiency   = (total_out / total_in * 100) if total_in else 0.0
        return {
            "total_received":   total_in,
            "total_disbursed":  total_out,
            "operational_cost": total_ops,
            "efficiency_pct":   round(efficiency, 2),
            "grade":            self._efficiency_grade(efficiency),
        }

    def zakat_summary(self) -> Dict[str, Any]:
        """ملخص حركة صندوق الزكاة."""
        report   = self.full_report()
        zakat_key = FundType.ZAKAT.value
        balances  = report.get("balances", {})
        return {
            "balance":          balances.get(zakat_key, 0.0),
            "total_received":   report.get("total_received",  0.0),
            "total_disbursed":  report.get("total_disbursed", 0.0),
            "beneficiaries":    sum(
                1 for a in self._eco._all_applications.values()
                if a.fund_type == FundType.ZAKAT
                and a.status.value == "تم الصرف"
            ),
        }

    def kpi_by_fund(self) -> List[Dict[str, Any]]:
        """مؤشرات الأداء لكل صندوق من الصناديق الأربعة."""
        report   = self.full_report()
        balances = report.get("balances", {})
        result   = []
        for ft in FundType:
            apps     = [
                a for a in self._eco._all_applications.values()
                if a.fund_type == ft
            ]
            disbursed = sum(
                a.approved_amount for a in apps
                if a.status.value == "تم الصرف"
            )
            result.append({
                "fund":       ft.value,
                "balance":    balances.get(ft.value, 0.0),
                "total_apps": len(apps),
                "disbursed":  disbursed,
            })
        return result

    # ── مساعدات ──────────────────────────────────────────────────────────────

    @staticmethod
    def _efficiency_grade(pct: float) -> str:
        if pct >= 90:
            return "ممتاز"
        if pct >= 75:
            return "جيد جداً"
        if pct >= 60:
            return "جيد"
        if pct >= 40:
            return "مقبول"
        return "يحتاج تحسين"


__all__ = ["FinanceReporter"]
