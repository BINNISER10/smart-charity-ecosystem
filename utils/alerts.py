"""
نظام التنبيهات الذكي — Smart Alerts System
===========================================
يراقب المنظومة ويُصدر تنبيهات في الحالات الحرجة:
  - طلبات تجاوزت 7 أيام دون قرار
  - صناديق أرصدتها أقل من عتبة الأمان
  - مستفيدون انتهت صلاحية تأهيلهم
  - طلبات بأولوية حرجة لم تُعالَج
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import TYPE_CHECKING, List, Dict, Any

if TYPE_CHECKING:
    from smart_charity_ecosystem import SmartCharityEcosystem

from smart_charity_ecosystem import ApplicationStatus, Priority, FundType


SAFETY_THRESHOLD_RATIO = 0.10   # تنبيه إذا انخفض الرصيد عن 10 % من الإجمالي
PENDING_DAYS_THRESHOLD  = 7     # تنبيه إذا تجاوز الطلب 7 أيام بلا قرار


@dataclass
class Alert:
    """نموذج تنبيه واحد."""

    level:   str          # "critical" | "warning" | "info"
    title:   str
    message: str
    ref_id:  str = ""
    date:    date = field(default_factory=date.today)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level":   self.level,
            "title":   self.title,
            "message": self.message,
            "ref_id":  self.ref_id,
            "date":    str(self.date),
        }


class AlertsSystem:
    """
    نظام التنبيهات الذكي للمنظومة الخيرية.

    الاستخدام::

        alerts = AlertsSystem(eco)
        for alert in alerts.generate():
            print(alert.title, alert.message)
    """

    def __init__(self, eco: "SmartCharityEcosystem") -> None:
        self._eco = eco

    # ── توليد التنبيهات ─────────────────────────────────────────────────────

    def generate(self) -> List[Alert]:
        """توليد جميع التنبيهات النشطة."""
        alerts: List[Alert] = []
        alerts.extend(self._check_pending_applications())
        alerts.extend(self._check_fund_balances())
        alerts.extend(self._check_critical_applications())
        alerts.extend(self._check_eligibility_expiry())
        return sorted(alerts, key=lambda a: ("critical", "warning", "info").index(a.level))

    def _check_pending_applications(self) -> List[Alert]:
        """تنبيه: طلبات معلّقة أكثر من 7 أيام."""
        pending_statuses = (
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.AI_ANALYZED,
            ApplicationStatus.PENDING_APPROVAL,
        )
        cutoff = date.today() - timedelta(days=PENDING_DAYS_THRESHOLD)
        result = []
        for a in self._eco._all_applications.values():
            if a.status in pending_statuses and a.submission_date < cutoff:
                days = (date.today() - a.submission_date).days
                result.append(Alert(
                    level   = "warning",
                    title   = "طلب متأخر",
                    message = f"الطلب {a.application_id} لم يُعالَج منذ {days} يوماً",
                    ref_id  = a.application_id,
                ))
        return result

    def _check_fund_balances(self) -> List[Alert]:
        """تنبيه: رصيد صندوق أقل من عتبة الأمان."""
        report = self._eco.finance.get_financial_report()
        total  = report.get("total_received", 0)
        result = []
        for fund_type in FundType:
            bal = report["balances"].get(fund_type.value, 0)
            if total > 0 and bal < total * SAFETY_THRESHOLD_RATIO:
                result.append(Alert(
                    level   = "critical",
                    title   = "رصيد منخفض",
                    message = f"صندوق {fund_type.value}: الرصيد {bal:,.0f} ريال (أقل من {SAFETY_THRESHOLD_RATIO*100:.0f}% من الإجمالي)",
                ))
        return result

    def _check_critical_applications(self) -> List[Alert]:
        """تنبيه: طلبات بأولوية حرجة لم تُعالَج."""
        pending_statuses = (
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.AI_ANALYZED,
            ApplicationStatus.PENDING_APPROVAL,
        )
        result = []
        for a in self._eco._all_applications.values():
            if a.status in pending_statuses and a.priority == Priority.CRITICAL:
                result.append(Alert(
                    level   = "critical",
                    title   = "طلب حرج بانتظار معالجة",
                    message = f"الطلب {a.application_id} — {a.sector.value} — أولوية حرجة",
                    ref_id  = a.application_id,
                ))
        return result

    def _check_eligibility_expiry(self) -> List[Alert]:
        """تنبيه: مستفيدون بحاجة لإعادة تقييم الأهلية (أكثر من سنة)."""
        cutoff = date.today() - timedelta(days=365)
        result = []
        for b in self._eco._beneficiaries.values():
            if b.is_eligible and b.registration_date < cutoff:
                result.append(Alert(
                    level   = "info",
                    title   = "تجديد أهلية مطلوب",
                    message = f"المستفيد {b.full_name} ({b.beneficiary_id}) — تسجيل قديم يحتاج مراجعة",
                    ref_id  = b.beneficiary_id,
                ))
        return result

    def summary(self) -> Dict[str, Any]:
        """ملخص إحصائي للتنبيهات."""
        alerts = self.generate()
        return {
            "total":    len(alerts),
            "critical": sum(1 for a in alerts if a.level == "critical"),
            "warning":  sum(1 for a in alerts if a.level == "warning"),
            "info":     sum(1 for a in alerts if a.level == "info"),
            "alerts":   [a.to_dict() for a in alerts],
        }


__all__ = ["Alert", "AlertsSystem"]
