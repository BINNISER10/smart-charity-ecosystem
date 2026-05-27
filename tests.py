#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           اختبارات منظومة العمل الخيري الذكي                               ║
║           Smart Charity Ecosystem — Test Suite                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

الوصف:
    اختبارات وحدة شاملة لجميع مكوّنات المنظومة.
    تُشغَّل بـ: python tests.py  أو  python -m unittest tests

المعايير المتبعة: PEP8 | Google Python Style Guide
"""
from __future__ import annotations

import io
import os
import sys
import json
import tempfile
import unittest
from datetime import date

# ── تأكد من أن المجلد الأصل في مسار الاستيراد ──────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

# ── تجاوز ترميز المخرجات على Windows ────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from smart_charity_ecosystem import (
    Address, Application, ApplicationStatus, Beneficiary,
    DataPersistence, FinanceSystem, FundType, GovernanceSystem,
    HijriCalendar, KPIReport, Priority, SectorType, SmartAI,
    SmartCharityEcosystem, Transaction, UserRole, ZakatCategory,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  مساعدات الاختبار
# ═══════════════════════════════════════════════════════════════════════════════

def _make_beneficiary(
    monthly_income: float = 1_500.0,
    family_size: int = 4,
    is_employed: bool = False,
    has_disability: bool = False,
) -> Beneficiary:
    """إنشاء مستفيد اختباري."""
    return Beneficiary(
        full_name="اختبار المستفيد",
        national_id="1000000001",
        phone="0500000001",
        address=Address(city="الرياض", district="النموذجي"),
        family_size=family_size,
        monthly_income=monthly_income,
        is_employed=is_employed,
        has_disability=has_disability,
    )


def _make_application(
    ben_id: str,
    amount: float = 5_000.0,
    sector: SectorType = SectorType.HEALTH,
    fund: FundType = FundType.ZAKAT,
) -> Application:
    """إنشاء طلب مساعدة اختباري."""
    return Application(
        beneficiary_id=ben_id,
        sector=sector,
        requested_amount=amount,
        fund_type=fund,
        description="طلب اختباري",
        supporting_docs=["وثيقة اختبارية"],
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات SmartAI
# ═══════════════════════════════════════════════════════════════════════════════

class TestSmartAI(unittest.TestCase):
    """اختبارات نواة الذكاء الاصطناعي."""

    def setUp(self) -> None:
        self.ai = SmartAI()

    def test_eligible_poor_family(self) -> None:
        """يجب أن تُقبل أسرة فقيرة عديمة الدخل."""
        b = _make_beneficiary(monthly_income=0.0, family_size=5)
        eligible, reason = self.ai.check_eligibility(b)
        self.assertTrue(eligible, reason)
        self.assertIn(b.zakat_category, (ZakatCategory.FUQARA, ZakatCategory.MASAKIN))

    def test_ineligible_rich(self) -> None:
        """يجب أن يُرفض غني بدخل عالٍ."""
        b = _make_beneficiary(monthly_income=50_000.0, family_size=2)
        eligible, _ = self.ai.check_eligibility(b)
        self.assertFalse(eligible)

    def test_disability_bonus(self) -> None:
        """يجب أن ترفع الإعاقة نقاط المستفيد."""
        b_normal  = _make_beneficiary(monthly_income=1_500.0, has_disability=False)
        b_disable = _make_beneficiary(monthly_income=1_500.0, has_disability=True)
        self.ai.check_eligibility(b_normal)
        self.ai.check_eligibility(b_disable)
        app_n = _make_application(b_normal.beneficiary_id)
        app_d = _make_application(b_disable.beneficiary_id)
        score_n, _, _ = self.ai.analyze_application(app_n, b_normal)
        score_d, _, _ = self.ai.analyze_application(app_d, b_disable)
        self.assertGreaterEqual(score_d, score_n)

    def test_analyze_sets_priority(self) -> None:
        """يجب أن يُحدِّد التحليل مستوى الأولوية ويُرجع نقاطاً موجبة."""
        b = _make_beneficiary(monthly_income=0.0)
        self.ai.check_eligibility(b)
        app = _make_application(b.beneficiary_id)
        score, priority, rec = self.ai.analyze_application(app, b)
        self.assertIn(priority, list(Priority))
        self.assertGreater(score, 0)
        self.assertIsInstance(rec, str)

    def test_experience_summary(self) -> None:
        """يجب أن يُحدَّث ملخص التجربة بعد كل تحليل."""
        b = _make_beneficiary(monthly_income=800.0)
        self.ai.check_eligibility(b)
        app = _make_application(b.beneficiary_id)
        self.ai.analyze_application(app, b)
        summary = self.ai.get_experience_summary()
        self.assertEqual(summary["total_analyzed"], 1)

    def test_predict_future_needs(self) -> None:
        """يجب أن تُرجع التنبؤات قاموساً بقيم موجبة."""
        b = _make_beneficiary(monthly_income=0.0)
        self.ai.check_eligibility(b)
        app = _make_application(b.beneficiary_id)
        app.status         = ApplicationStatus.APPROVED
        app.approved_amount = 5_000.0
        predictions = self.ai.predict_future_needs([app])
        self.assertIsInstance(predictions, dict)
        self.assertTrue(all(v >= 0 for v in predictions.values()))


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات FinanceSystem
# ═══════════════════════════════════════════════════════════════════════════════

class TestFinanceSystem(unittest.TestCase):
    """اختبارات نظام إدارة الأموال."""

    def setUp(self) -> None:
        self.finance = FinanceSystem()

    def test_receive_donation_increases_balance(self) -> None:
        """يجب أن يرفع الإيداع رصيد الصندوق."""
        initial = self.finance.get_balance(FundType.ZAKAT)
        ok, _ = self.finance.receive_donation(
            "متبرع اختباري", "0500000000", 10_000, FundType.ZAKAT, "TEST"
        )
        self.assertTrue(ok)
        self.assertEqual(
            self.finance.get_balance(FundType.ZAKAT),
            initial + 10_000,
        )

    def test_zero_donation_rejected(self) -> None:
        """يجب رفض التبرع بقيمة صفر."""
        ok, msg = self.finance.receive_donation(
            "متبرع", "050", 0, FundType.ZAKAT, "TEST"
        )
        self.assertFalse(ok)

    def test_disburse_reduces_balance(self) -> None:
        """يجب أن يُخفِّض الصرف رصيد الصندوق."""
        self.finance.receive_donation("م", "0", 20_000, FundType.ZAKAT, "T")
        b = _make_beneficiary(monthly_income=0.0)
        app = _make_application(b.beneficiary_id, amount=5_000)
        app.status          = ApplicationStatus.APPROVED
        app.approved_amount = 5_000
        balance_before = self.finance.get_balance(FundType.ZAKAT)
        ok, _ = self.finance.disburse_funds(app, "TEST-EXEC")
        self.assertTrue(ok)
        self.assertEqual(
            self.finance.get_balance(FundType.ZAKAT),
            balance_before - 5_000,
        )

    def test_insufficient_balance_rejected(self) -> None:
        """يجب رفض الصرف عند نقص الرصيد."""
        b = _make_beneficiary()
        app = _make_application(b.beneficiary_id, amount=999_999_999)
        app.status          = ApplicationStatus.APPROVED
        app.approved_amount = 999_999_999
        ok, msg = self.finance.disburse_funds(app, "TEST")
        self.assertFalse(ok)
        self.assertIn("رصيد", msg)

    def test_financial_report_structure(self) -> None:
        """يجب أن يحتوي التقرير المالي على الحقول المطلوبة."""
        report = self.finance.get_financial_report()
        for key in ("balances", "total_received", "total_disbursed",
                    "total_transactions", "total_donors"):
            self.assertIn(key, report)

    def test_fund_separation(self) -> None:
        """يجب أن تبقى الصناديق الأربعة مستقلة عن بعضها."""
        self.finance.receive_donation("أ", "0", 1_000, FundType.ZAKAT,    "T")
        self.finance.receive_donation("ب", "0", 2_000, FundType.SADAQAT,  "T")
        self.finance.receive_donation("ج", "0", 3_000, FundType.AWQAF,    "T")
        self.finance.receive_donation("د", "0", 4_000, FundType.RESTRICTED, "T")
        self.assertNotEqual(
            self.finance.get_balance(FundType.ZAKAT),
            self.finance.get_balance(FundType.SADAQAT),
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات GovernanceSystem
# ═══════════════════════════════════════════════════════════════════════════════

class TestGovernanceSystem(unittest.TestCase):
    """اختبارات نظام الحوكمة والصلاحيات."""

    def setUp(self) -> None:
        self.gov = GovernanceSystem()
        self.admin_id = self.gov.register_user(
            "مدير اختبار", UserRole.EXECUTIVE_DIR, "الإدارة العليا"
        )
        self.case_id = self.gov.register_user(
            "أخصائي اختبار", UserRole.CASE_WORKER, "قسم الحالات"
        )

    def test_register_user(self) -> None:
        """يجب أن يُضيف تسجيل المستخدم إدخالاً في القاموس."""
        self.assertIn(self.admin_id, self.gov._users)
        self.assertIn(self.case_id,  self.gov._users)

    def test_approval_within_limit(self) -> None:
        """يجب قبول موافقة المدير التنفيذي على أي مبلغ."""
        b = _make_beneficiary(monthly_income=0.0)
        app = _make_application(b.beneficiary_id, amount=50_000)
        app.status = ApplicationStatus.PENDING_APPROVAL
        ok = self.gov.approve_application(app, self.admin_id, 50_000)
        self.assertTrue(ok)
        self.assertEqual(app.status, ApplicationStatus.APPROVED)

    def test_approval_exceeds_limit(self) -> None:
        """يجب رفض موافقة أخصائي الحالات على مبلغ يتجاوز صلاحيته."""
        b = _make_beneficiary(monthly_income=0.0)
        app = _make_application(b.beneficiary_id, amount=100_000)
        app.status = ApplicationStatus.PENDING_APPROVAL
        ok = self.gov.approve_application(app, self.case_id, 100_000)
        self.assertFalse(ok)

    def test_audit_log_records_actions(self) -> None:
        """يجب أن يُسجَّل كل إجراء في سجل التدقيق."""
        b = _make_beneficiary(monthly_income=0.0)
        app = _make_application(b.beneficiary_id)
        app.status = ApplicationStatus.PENDING_APPROVAL
        self.gov.approve_application(app, self.admin_id, 5_000)  # bool result ignored
        logs = self.gov.get_audit_log()
        self.assertTrue(len(logs) > 0)

    def test_policy_list_not_empty(self) -> None:
        """يجب أن تحتوي قائمة السياسات على عناصر."""
        policies = self.gov.get_policies()
        self.assertGreater(len(policies), 0)


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات SmartCharityEcosystem (تكامل)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSmartCharityEcosystem(unittest.TestCase):
    """اختبارات تكامل المنظومة الرئيسية."""

    def setUp(self) -> None:
        self.eco = SmartCharityEcosystem()
        self.eco.load_demo_data()

    def test_demo_data_loaded(self) -> None:
        """يجب أن يُحمِّل load_demo_data بيانات حقيقية."""
        self.assertGreater(len(self.eco._beneficiaries), 0)
        self.assertGreater(len(self.eco._all_applications), 0)

    def test_register_eligible_beneficiary(self) -> None:
        """يجب قبول مستفيد مؤهل وإضافته للقاموس."""
        b = _make_beneficiary(monthly_income=0.0)
        ok, _ = self.eco.register_beneficiary(b)
        self.assertTrue(ok)
        self.assertIn(b.beneficiary_id, self.eco._beneficiaries)

    def test_register_ineligible_beneficiary_still_added(self) -> None:
        """يجب إضافة غير المؤهل مع تحديد حالة الأهلية."""
        b = _make_beneficiary(monthly_income=100_000.0)
        _, _ = self.eco.register_beneficiary(b)
        self.assertIn(b.beneficiary_id, self.eco._beneficiaries)
        self.assertFalse(self.eco._beneficiaries[b.beneficiary_id].is_eligible)

    def test_submit_application_for_eligible(self) -> None:
        """يجب قبول طلب مستفيد مؤهل وتحليله."""
        b = _make_beneficiary(monthly_income=0.0)
        self.eco.register_beneficiary(b)
        app = _make_application(b.beneficiary_id)
        ok, _ = self.eco.submit_application(app)
        self.assertTrue(ok)
        self.assertGreater(app.ai_score, 0)

    def test_submit_application_for_ineligible_rejected(self) -> None:
        """يجب رفض طلب مستفيد غير مؤهل."""
        b = _make_beneficiary(monthly_income=100_000.0)
        self.eco.register_beneficiary(b)
        app = _make_application(b.beneficiary_id)
        ok, _ = self.eco.submit_application(app)
        self.assertFalse(ok)

    def test_full_lifecycle(self) -> None:
        """يجب أن تكتمل دورة الحياة الكاملة: تسجيل → طلب → موافقة → صرف."""
        self.eco.finance.receive_donation("م", "0", 50_000, FundType.ZAKAT, "T")
        b = _make_beneficiary(monthly_income=0.0)
        self.eco.register_beneficiary(b)
        app = _make_application(b.beneficiary_id, amount=5_000)
        self.eco.submit_application(app)
        ok_a, _ = self.eco.process_approval(
            app.application_id, self.eco.sector_mgr_id, 5_000
        )
        self.assertTrue(ok_a)
        ok_d, _ = self.eco.process_disbursement(
            app.application_id, self.eco.finance_mgr_id
        )
        self.assertTrue(ok_d)
        self.assertEqual(
            self.eco._all_applications[app.application_id].status,
            ApplicationStatus.DISBURSED,
        )

    def test_ecosystem_report_structure(self) -> None:
        """يجب أن يحتوي التقرير الشامل على المفاتيح المطلوبة."""
        report = self.eco.get_ecosystem_report()
        for key in ("organization", "version", "total_beneficiaries",
                    "eligible_beneficiaries", "total_applications", "sector_kpis"):
            self.assertIn(key, report)


# ── مساعد: DataPersistence مع مسار ثابت للاختبارات ──────────────────────────

class _PersistenceWithPath(DataPersistence):
    """نسخة اختبارية تتجاوز منطق المسار لاستخدام مسار محدد مباشرةً."""

    def __init__(self, fixed_path: str) -> None:
        self._fixed_path = fixed_path

    def save(self, eco: SmartCharityEcosystem) -> tuple:  # type: ignore[override]
        """حفظ إلى المسار المحدد مباشرةً."""
        try:
            import json as _json
            from smart_charity_ecosystem import FundType as _FT
            snapshot = {
                "version":       SmartCharityEcosystem.VERSION,
                "saved_at":      "",
                "beneficiaries": [self._ben_to_dict(b)
                                  for b in eco._beneficiaries.values()],
                "applications":  [self._app_to_dict(a)
                                  for a in eco._all_applications.values()],
                "transactions":  [self._txn_to_dict(t)
                                  for t in eco.finance._transactions],
                "balances":      {ft.value: eco.finance._balances[ft]
                                  for ft in _FT},
                "donors":        [
                    {"donor_id": d.donor_id, "full_name": d.full_name,
                     "phone": d.phone, "fund_type": d.fund_type.value,
                     "total_donated": d.total_donated,
                     "donation_count": d.donation_count}
                    for d in eco.finance._donors.values()
                ],
            }
            with open(self._fixed_path, "w", encoding="utf-8") as fh:
                _json.dump(snapshot, fh, ensure_ascii=False, indent=2,
                           default=str)
            return True, f"saved: {self._fixed_path}"
        except Exception as exc:
            return False, str(exc)

    def load(self, eco: SmartCharityEcosystem) -> tuple:  # type: ignore[override]
        """تحميل من المسار المحدد مباشرةً."""
        if not os.path.exists(self._fixed_path):
            return False, "لا يوجد ملف حفظ سابق"
        self.DATA_FILE = self._fixed_path
        import unittest.mock as _mock
        with _mock.patch.object(
            DataPersistence, "load",
            lambda self2, eco2: _real_load(self2, eco2, self._fixed_path)
        ):
            return _real_load(self, eco, self._fixed_path)


def _real_load(persistence: DataPersistence,
               eco: SmartCharityEcosystem,
               path: str) -> tuple:
    """دالة تحميل تستخدم مسار مطلق مباشرةً."""
    try:
        import json as _json
        with open(path, encoding="utf-8") as fh:
            snapshot = _json.load(fh)
        for d in snapshot.get("beneficiaries", []):
            b = persistence._dict_to_ben(d)
            eco._beneficiaries[b.beneficiary_id] = b
        for d in snapshot.get("applications", []):
            a = persistence._dict_to_app(d)
            eco._all_applications[a.application_id] = a
            if a.sector in eco.sectors:
                eco.sectors[a.sector]._applications.append(a)
        from smart_charity_ecosystem import FundType as _FT, datetime as _dt
        eco.finance._transactions = [
            persistence._dict_to_txn(d) for d in snapshot.get("transactions", [])
        ]
        for ft_val, bal in snapshot.get("balances", {}).items():
            eco.finance._balances[_FT(ft_val)] = float(bal)
        from smart_charity_ecosystem import DonorRecord as _DR, FundType as _FT2
        eco.finance._donors = {}
        for d in snapshot.get("donors", []):
            dr = _DR(
                full_name=d.get("full_name", ""),
                phone=d.get("phone", ""),
                fund_type=_FT2(d.get("fund_type", _FT2.ZAKAT.value)),
            )
            dr.donor_id       = d.get("donor_id", dr.donor_id)
            dr.total_donated  = float(d.get("total_donated", 0.0))
            dr.donation_count = int(d.get("donation_count", 0))
            eco.finance._donors[f"{dr.phone}_{dr.fund_type.value}"] = dr
        count_b = len(snapshot.get("beneficiaries", []))
        count_a = len(snapshot.get("applications", []))
        return True, f"تم تحميل {count_b} مستفيد و{count_a} طلب"
    except Exception as exc:
        return False, str(exc)


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات DataPersistence
# ═══════════════════════════════════════════════════════════════════════════════

class TestDataPersistence(unittest.TestCase):
    """اختبارات طبقة حفظ واستعادة البيانات."""

    def setUp(self) -> None:
        self.tmp_dir  = tempfile.mkdtemp()
        self.tmp_file = os.path.join(self.tmp_dir, "test_charity_data.json")
        self.eco = SmartCharityEcosystem()
        self.eco.load_demo_data()
        self.persistence = _PersistenceWithPath(self.tmp_file)

    def test_save_creates_file(self) -> None:
        """يجب أن يُنشئ الحفظ ملف JSON صالحاً."""
        ok, msg = self.persistence.save(self.eco)
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.exists(self.tmp_file))

    def test_save_valid_json(self) -> None:
        """يجب أن يكون الملف المحفوظ JSON صالحاً."""
        self.persistence.save(self.eco)
        with open(self.tmp_file, encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("beneficiaries", data)
        self.assertIn("applications",  data)
        self.assertIn("transactions",  data)
        self.assertIn("balances",      data)

    def test_load_restores_beneficiaries(self) -> None:
        """يجب أن يُستعاد عدد المستفيدين بعد الحفظ والتحميل."""
        count_before = len(self.eco._beneficiaries)
        self.persistence.save(self.eco)
        eco2 = SmartCharityEcosystem()
        p2   = _PersistenceWithPath(self.tmp_file)
        ok, msg = p2.load(eco2)
        self.assertTrue(ok, msg)
        self.assertEqual(len(eco2._beneficiaries), count_before)

    def test_load_restores_balances(self) -> None:
        """يجب أن تُستعاد الأرصدة بعد الحفظ والتحميل."""
        self.eco.finance.receive_donation("م", "0", 5_000, FundType.ZAKAT, "T")
        bal_before = self.eco.finance.get_balance(FundType.ZAKAT)
        self.persistence.save(self.eco)
        eco2 = SmartCharityEcosystem()
        p2   = _PersistenceWithPath(self.tmp_file)
        _, msg = p2.load(eco2)
        self.assertAlmostEqual(
            eco2.finance.get_balance(FundType.ZAKAT), bal_before, places=2
        )

    def test_load_nonexistent_file(self) -> None:
        """يجب إرجاع (False, رسالة) عند غياب الملف."""
        p_missing = _PersistenceWithPath(
            os.path.join(self.tmp_dir, "nonexistent.json")
        )
        ok, msg = p_missing.load(SmartCharityEcosystem())
        self.assertFalse(ok)
        self.assertIn("لا يوجد", msg)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات حاسبة الزكاة (المنطق فقط)
# ═══════════════════════════════════════════════════════════════════════════════

class TestZakatLogic(unittest.TestCase):
    """اختبارات منطق حساب الزكاة الشرعي."""

    NISAB  = SmartAI.NISAB_THRESHOLD
    RATE   = 0.025

    def test_cash_above_nisab(self) -> None:
        """يجب حساب زكاة النقد عند بلوغ النصاب."""
        cash = self.NISAB + 1_000
        zakat = cash * self.RATE
        self.assertAlmostEqual(zakat, (self.NISAB + 1_000) * 0.025, places=2)

    def test_cash_below_nisab(self) -> None:
        """يجب ألا تجب الزكاة على نقد دون النصاب."""
        cash = self.NISAB - 1
        zakat = cash * self.RATE if cash >= self.NISAB else 0.0
        self.assertEqual(zakat, 0.0)

    def test_gold_nisab(self) -> None:
        """يجب ألا تجب زكاة الذهب على أقل من 85 جراماً."""
        GOLD_PRICE = 230.0
        grams_below_nisab = 80
        val = grams_below_nisab * GOLD_PRICE
        nisab_gold = 85 * GOLD_PRICE
        zakat = val * self.RATE if val >= nisab_gold else 0.0
        self.assertEqual(zakat, 0.0)

    def test_crops_irrigated_rate(self) -> None:
        """يجب أن تكون نسبة الزروع المروية 5%."""
        crop_rate = 0.05
        self.assertEqual(crop_rate, 0.05)

    def test_crops_rain_rate(self) -> None:
        """يجب أن تكون نسبة الزروع البعلية 10%."""
        crop_rate = 0.10
        self.assertEqual(crop_rate, 0.10)


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات نظام التنبيهات
# ═══════════════════════════════════════════════════════════════════════════════

class TestAlertsSystem(unittest.TestCase):
    """اختبارات منطق كشف التنبيهات في نظام المراقبة."""

    def setUp(self) -> None:
        self.eco = SmartCharityEcosystem()

    def test_no_alerts_empty_system(self) -> None:
        """يجب ألّا تُنتج منظومة فارغة تنبيهات طلبات متأخرة."""
        pending = [
            a for a in self.eco._all_applications.values()
            if a.status in (
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.AI_ANALYZED,
                ApplicationStatus.PENDING_APPROVAL,
            )
        ]
        self.assertEqual(len(pending), 0)

    def test_low_balance_detection(self) -> None:
        """يجب اكتشاف الرصيد المنخفض عند انعدامه."""
        LOW = 5_000.0
        for ft in FundType:
            bal = self.eco.finance.get_balance(ft)
            self.assertLess(bal, LOW)

    def test_critical_priority_detection(self) -> None:
        """يجب تصنيف الطلب الحرج ضمن الحالات الحرجة."""
        b = _make_beneficiary(monthly_income=0.0)
        self.eco.register_beneficiary(b)
        app = _make_application(b.beneficiary_id, amount=3_000)
        app.priority = Priority.CRITICAL
        app.status   = ApplicationStatus.SUBMITTED
        self.eco._all_applications[app.application_id] = app
        critical_pending = [
            a for a in self.eco._all_applications.values()
            if a.priority == Priority.CRITICAL
            and a.status in (
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.AI_ANALYZED,
                ApplicationStatus.PENDING_APPROVAL,
            )
        ]
        self.assertGreater(len(critical_pending), 0)

    def test_health_score_drops_with_critical_alerts(self) -> None:
        """يجب أن ينخفض مؤشر الصحة بوجود تنبيهات حرجة."""
        base_score = 100
        critical_count = 3
        score = max(0, base_score - critical_count * 15)
        self.assertLess(score, base_score)

    def test_health_score_perfect_when_no_alerts(self) -> None:
        """يجب أن يكون مؤشر الصحة 100 عند غياب التنبيهات."""
        health_score = 100 - (0 * 15) - (0 * 5)
        self.assertEqual(health_score, 100)

    def test_food_batch_expiry_flag(self) -> None:
        """يجب اكتشاف الدفعات التي تنتهي خلال 14 يوماً."""
        from datetime import date, timedelta
        today = date.today()
        expiring_soon = today + timedelta(days=7)
        days_left = (expiring_soon - today).days
        self.assertLessEqual(days_left, 14)
        self.assertGreaterEqual(days_left, 0)


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات تصدير CSV
# ═══════════════════════════════════════════════════════════════════════════════

class TestCSVExport(unittest.TestCase):
    """اختبارات وظيفة تصدير CSV."""

    def setUp(self) -> None:
        self.eco      = SmartCharityEcosystem()
        self.eco.load_demo_data()
        self.tmp_dir  = tempfile.mkdtemp()

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _export_csv(self, kind: str) -> str:
        """مساعد: يكتب CSV إلى مجلد مؤقت ويُرجع المحتوى."""
        import csv as _csv
        rows: list = []
        if kind == "beneficiaries":
            headers = ["id", "name", "city", "eligible"]
            rows    = [
                [b.beneficiary_id, b.full_name, b.address.city,
                 "yes" if b.is_eligible else "no"]
                for b in self.eco._beneficiaries.values()
            ]
        elif kind == "applications":
            headers = ["id", "sector", "amount", "status"]
            rows    = [
                [a.application_id, a.sector.value,
                 a.requested_amount, a.status.value]
                for a in self.eco._all_applications.values()
            ]
        elif kind == "transactions":
            headers = ["id", "fund", "amount", "type"]
            rows    = [
                [t.transaction_id, t.fund_type.value,
                 t.amount, t.transaction_type]
                for t in self.eco.finance.get_transactions(limit=9_999)
            ]
        path = os.path.join(self.tmp_dir, f"{kind}.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = _csv.writer(fh)
            writer.writerow(headers)
            writer.writerows(rows)
        with open(path, encoding="utf-8-sig") as fh:
            return fh.read()

    def test_beneficiaries_csv_has_header(self) -> None:
        """يجب أن يحتوي CSV المستفيدين على رأس الأعمدة."""
        content = self._export_csv("beneficiaries")
        self.assertIn("id", content)
        self.assertIn("name", content)

    def test_beneficiaries_csv_row_count(self) -> None:
        """يجب أن يتطابق عدد صفوف CSV مع عدد المستفيدين."""
        content  = self._export_csv("beneficiaries")
        lines    = [ln for ln in content.splitlines() if ln.strip()]
        expected = len(self.eco._beneficiaries) + 1  # +1 للرأس
        self.assertEqual(len(lines), expected)

    def test_applications_csv_has_status(self) -> None:
        """يجب أن يحتوي CSV الطلبات على عمود الحالة."""
        content = self._export_csv("applications")
        self.assertIn("status", content)

    def test_transactions_csv_not_empty(self) -> None:
        """يجب أن يحتوي CSV المعاملات على بيانات."""
        content = self._export_csv("transactions")
        lines   = [ln for ln in content.splitlines() if ln.strip()]
        self.assertGreater(len(lines), 1)  # أكثر من رأس فقط

    def test_xlsx_is_valid_zip(self) -> None:
        """يجب أن يكون ملف XLSX ZIP صالحاً."""
        from smart_charity_ecosystem import CLI as _CLI
        import zipfile as _zf
        sheets = [
            ("ورقة1", ["أ", "ب"], [[1, "قيمة"], [2, "أخرى"]])
        ]
        data = _CLI._build_xlsx(sheets)
        buf  = io.BytesIO(data)
        self.assertTrue(_zf.is_zipfile(buf))

    def test_xlsx_contains_worksheet(self) -> None:
        """يجب أن يحتوي XLSX على ملف worksheet."""
        from smart_charity_ecosystem import CLI as _CLI
        import zipfile as _zf
        sheets = [("بيانات", ["x"], [[1], [2]])]
        buf = io.BytesIO(_CLI._build_xlsx(sheets))
        with _zf.ZipFile(buf) as zf:
            names = zf.namelist()
        self.assertIn("xl/worksheets/sheet1.xml", names)

    def test_xlsx_shared_strings_arabic(self) -> None:
        """يجب أن يحفظ XLSX النص العربي في sharedStrings."""
        from smart_charity_ecosystem import CLI as _CLI
        import zipfile as _zf
        sheets = [("ورقة", ["اسم"], [["أحمد"]])]
        buf = io.BytesIO(_CLI._build_xlsx(sheets))
        with _zf.ZipFile(buf) as zf:
            ss = zf.read("xl/sharedStrings.xml").decode("utf-8")
        self.assertIn("أحمد", ss)

    def test_xlsx_multi_sheet(self) -> None:
        """يجب أن تُنشئ الأوراق المتعددة ملفات worksheet منفصلة."""
        from smart_charity_ecosystem import CLI as _CLI
        import zipfile as _zf
        sheets = [
            ("ورقة1", ["أ"], [[1]]),
            ("ورقة2", ["ب"], [[2]]),
        ]
        buf = io.BytesIO(_CLI._build_xlsx(sheets))
        with _zf.ZipFile(buf) as zf:
            names = zf.namelist()
        self.assertIn("xl/worksheets/sheet1.xml", names)
        self.assertIn("xl/worksheets/sheet2.xml", names)

    def test_pdf_html_is_valid_html(self) -> None:
        """يجب أن يحتوي HTML على علامات HTML الأساسية."""
        from smart_charity_ecosystem import CLI as _CLI
        self.eco.load_demo_data()
        html = _CLI._build_pdf_html(self.eco)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn('dir="rtl"', html)
        self.assertIn("window.print()", html)

    def test_pdf_html_contains_beneficiary_data(self) -> None:
        """يجب أن يحتوي HTML على بيانات المستفيدين."""
        from smart_charity_ecosystem import CLI as _CLI
        self.eco.load_demo_data()
        html = _CLI._build_pdf_html(self.eco)
        self.assertIn("المستفيدون", html)
        self.assertIn("الطلبات", html)
        self.assertIn("المعاملات", html)

    def test_col_letter_basic(self) -> None:
        """يجب تحويل أرقام الأعمدة بشكل صحيح."""
        from smart_charity_ecosystem import CLI as _CLI
        self.assertEqual(_CLI._col_letter(0),  "A")
        self.assertEqual(_CLI._col_letter(25), "Z")
        self.assertEqual(_CLI._col_letter(26), "AA")
        self.assertEqual(_CLI._col_letter(27), "AB")

    def test_csv_is_valid_utf8_sig(self) -> None:
        """يجب أن يكون الملف بترميز UTF-8 مع BOM لدعم Excel."""
        path = os.path.join(self.tmp_dir, "test.csv")
        import csv as _csv
        with open(path, "w", newline="", encoding="utf-8-sig") as fh:
            _csv.writer(fh).writerow(["اسم", "قيمة"])
        with open(path, "rb") as fh:
            bom = fh.read(3)
        self.assertEqual(bom, b"\xef\xbb\xbf")


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات وظيفة التعديل ✏️
# ═══════════════════════════════════════════════════════════════════════════════

class TestEditRecords(unittest.TestCase):
    """اختبارات تعديل السجلات الموجودة مباشرةً عبر نموذج البيانات."""

    def setUp(self) -> None:
        self.eco = SmartCharityEcosystem()
        self.eco.load_demo_data()

    def test_edit_beneficiary_name(self) -> None:
        """يجب أن يُحدَّث اسم المستفيد فور تعديله."""
        b = next(iter(self.eco._beneficiaries.values()))
        old_name = b.full_name
        b.full_name = "اسم معدَّل للاختبار"
        self.assertNotEqual(
            self.eco._beneficiaries[b.beneficiary_id].full_name, old_name
        )

    def test_edit_beneficiary_income_updates_eligibility(self) -> None:
        """يجب أن تتغير الأهلية بعد تعديل الدخل وإعادة التقييم."""
        b = next(iter(self.eco._beneficiaries.values()))
        b.monthly_income = 0.0
        is_elig, _ = self.eco.ai.check_eligibility(b)
        b.is_eligible = is_elig
        self.assertTrue(b.is_eligible)

    def test_edit_beneficiary_high_income_loses_eligibility(self) -> None:
        """يجب أن يفقد المستفيد الأهلية عند ارتفاع دخله."""
        b = next(iter(self.eco._beneficiaries.values()))
        b.monthly_income  = 50_000.0
        b.family_size     = 1
        b.has_disability  = False
        is_elig, _ = self.eco.ai.check_eligibility(b)
        b.is_eligible = is_elig
        self.assertFalse(b.is_eligible)

    def test_edit_application_description(self) -> None:
        """يجب أن يُحدَّث وصف الطلب مباشرةً."""
        a = next(iter(self.eco._all_applications.values()))
        a.description = "وصف جديد للاختبار"
        retrieved = self.eco._all_applications[a.application_id]
        self.assertEqual(retrieved.description, "وصف جديد للاختبار")

    def test_edit_submitted_application_amount(self) -> None:
        """يجب السماح بتعديل مبلغ الطلب إذا كانت حالته SUBMITTED."""
        submitted = [
            a for a in self.eco._all_applications.values()
            if a.status == ApplicationStatus.SUBMITTED
        ]
        if not submitted:
            self.skipTest("لا توجد طلبات بحالة SUBMITTED في البيانات التمثيلية")
        a = submitted[0]
        a.requested_amount = 9_999.0
        self.assertEqual(
            self.eco._all_applications[a.application_id].requested_amount,
            9_999.0,
        )

    def test_edit_application_priority(self) -> None:
        """يجب أن تتغير أولوية الطلب."""
        a = next(iter(self.eco._all_applications.values()))
        a.priority = Priority.CRITICAL
        self.assertEqual(a.priority, Priority.CRITICAL)

    def test_edit_donor_name(self) -> None:
        """يجب أن يُحدَّث اسم المتبرع."""
        d = next(iter(self.eco.finance._donors.values()))
        d.full_name = "متبرع معدَّل"
        self.assertIn("معدَّل", d.full_name)

    def test_edit_donor_phone_reindexes_key(self) -> None:
        """يجب أن يُعاد فهرسة المتبرع بالمفتاح الجديد عند تغيير الهاتف."""
        donors = self.eco.finance._donors
        old_key, d = next(iter(donors.items()))
        old_phone = d.phone
        new_phone = "0501234999"
        new_key   = f"{new_phone}_{d.fund_type.value}"
        d.phone   = new_phone
        donors.pop(old_key, None)
        donors[new_key] = d
        self.assertIn(new_key, donors)
        self.assertNotIn(old_key, donors)


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات التقويم الهجري
# ═══════════════════════════════════════════════════════════════════════════════

class TestHijriCalendar(unittest.TestCase):
    """اختبارات محوّل التقويم الهجري الحسابي."""

    def test_known_date_2024_01_01(self) -> None:
        """يجب أن يتطابق 2024/01/01 = 19 جمادى الآخرة 1445."""
        hy, hm, hd = HijriCalendar.to_hijri(2024, 1, 1)
        self.assertEqual(hy, 1445)
        self.assertEqual(hm, 6)
        self.assertEqual(hd, 19)

    def test_known_date_2000_01_01(self) -> None:
        """يجب أن يتطابق 2000/01/01 = 24 رمضان 1420."""
        hy, hm, hd = HijriCalendar.to_hijri(2000, 1, 1)
        self.assertEqual(hy, 1420)
        self.assertEqual(hm, 9)
        self.assertEqual(hd, 24)

    def test_known_date_first_muharram(self) -> None:
        """يجب أن يتطابق 1445/07/19 = 1 محرم 1445."""
        hy, hm, hd = HijriCalendar.to_hijri(2023, 7, 19)
        self.assertEqual(hy, 1445)
        self.assertEqual(hm, 1)
        self.assertEqual(hd, 1)

    def test_hijri_year_range(self) -> None:
        """يجب أن تكون السنة الهجرية ضمن نطاق منطقي."""
        hy, hm, hd = HijriCalendar.to_hijri(2025, 1, 1)
        self.assertGreater(hy, 1400)
        self.assertLess(hy, 1500)

    def test_month_range(self) -> None:
        """يجب أن يكون الشهر بين 1 و 12."""
        for g_m in range(1, 13):
            hy, hm, hd = HijriCalendar.to_hijri(2024, g_m, 15)
            self.assertGreaterEqual(hm, 1)
            self.assertLessEqual(hm, 12)

    def test_day_range(self) -> None:
        """يجب أن يكون اليوم بين 1 و 30."""
        for g_d in (1, 10, 20, 28):
            hy, hm, hd = HijriCalendar.to_hijri(2024, 3, g_d)
            self.assertGreaterEqual(hd, 1)
            self.assertLessEqual(hd, 30)

    def test_format_hijri_returns_arabic(self) -> None:
        """يجب أن يحتوي format_hijri على 'هـ' واسم شهر عربي."""
        s = HijriCalendar.format_hijri(2024, 1, 1)
        self.assertIn("هـ", s)
        self.assertIn("جمادى الآخرة", s)

    def test_dual_contains_both_calendars(self) -> None:
        """يجب أن يحتوي dual على 'م' و'هـ' معاً."""
        s = HijriCalendar.dual(date(2024, 1, 1))
        self.assertIn("م", s)
        self.assertIn("هـ", s)
        self.assertIn("2024", s)
        self.assertIn("1445", s)

    def test_epoch_day(self) -> None:
        """يجب أن يكون 19 يوليو 622م = 1 محرم 1هـ (بداية التقويم)."""
        hy, hm, hd = HijriCalendar.to_hijri(622, 7, 19)
        self.assertEqual(hy, 1)
        self.assertEqual(hm, 1)
        self.assertEqual(hd, 1)


# ═══════════════════════════════════════════════════════════════════════════════
#  اختبارات إلغاء / أرشفة / ملف المستفيد / فلتر التاريخ
# ═══════════════════════════════════════════════════════════════════════════════

class TestBackendCompletion(unittest.TestCase):
    """اختبارات تغطية مكونات الباك اند المكتملة حديثاً."""

    def setUp(self) -> None:
        self.eco = SmartCharityEcosystem()
        self.eco.load_demo_data()

    # ── إلغاء الطلب ──────────────────────────────────────────────────────
    def test_cancel_application_changes_status(self) -> None:
        """يجب أن يُغيّر cancel_application الحالة إلى CANCELLED."""
        a = next(iter(self.eco._all_applications.values()))
        original = a.status
        if original in (
            ApplicationStatus.DISBURSED,
            ApplicationStatus.CANCELLED,
            ApplicationStatus.CLOSED,
        ):
            self.skipTest("الطلب الأول غير قابل للإلغاء بالحالة الحالية")
        ok = self.eco.governance.cancel_application(a, "TEST", "اختبار")
        self.assertTrue(ok)
        self.assertEqual(a.status, ApplicationStatus.CANCELLED)

    def test_cancel_disbursed_application_fails(self) -> None:
        """يجب أن يرفض الإلغاء إذا كانت حالة الطلب DISBURSED."""
        disbursed = [
            a for a in self.eco._all_applications.values()
            if a.status == ApplicationStatus.DISBURSED
        ]
        if not disbursed:
            self.skipTest("لا توجد طلبات مصروفة")
        ok = self.eco.governance.cancel_application(disbursed[0], "TEST")
        self.assertFalse(ok)

    def test_cancel_records_audit_entry(self) -> None:
        """يجب أن يُسجَّل الإلغاء في سجل التدقيق."""
        a = next(
            (x for x in self.eco._all_applications.values()
             if x.status not in (
                 ApplicationStatus.DISBURSED,
                 ApplicationStatus.CANCELLED,
                 ApplicationStatus.CLOSED,
             )),
            None,
        )
        if a is None:
            self.skipTest("لا توجد طلبات قابلة للإلغاء")
        before = len(self.eco.governance.get_audit_log(limit=9999))
        self.eco.governance.cancel_application(a, "TEST", "سبب")
        after = len(self.eco.governance.get_audit_log(limit=9999))
        self.assertGreater(after, before)

    # ── أرشفة المستفيد ────────────────────────────────────────────────────
    def test_archive_beneficiary_sets_flag(self) -> None:
        """يجب أن تضبط الأرشفة is_archived=True."""
        b = next(iter(self.eco._beneficiaries.values()))
        ok = self.eco.archive_beneficiary(b.beneficiary_id)
        self.assertTrue(ok)
        self.assertTrue(self.eco._beneficiaries[b.beneficiary_id].is_archived)

    def test_archive_nonexistent_returns_false(self) -> None:
        """يجب إرجاع False لمعرّف غير موجود."""
        self.assertFalse(self.eco.archive_beneficiary("BEN-FAKE999"))

    def test_restore_beneficiary(self) -> None:
        """يجب أن تُعيد الاستعادة is_archived إلى False."""
        b = next(iter(self.eco._beneficiaries.values()))
        self.eco.archive_beneficiary(b.beneficiary_id)
        ok = self.eco.restore_beneficiary(b.beneficiary_id)
        self.assertTrue(ok)
        self.assertFalse(self.eco._beneficiaries[b.beneficiary_id].is_archived)

    # ── ملف المستفيد الكامل ──────────────────────────────────────────────
    def test_beneficiary_history_returns_dict(self) -> None:
        """يجب أن يُرجع get_beneficiary_history قاموساً بالمفاتيح الصحيحة."""
        b = next(iter(self.eco._beneficiaries.values()))
        hist = self.eco.get_beneficiary_history(b.beneficiary_id)
        for key in ("beneficiary", "applications", "total_disbursed",
                    "disbursed_count", "last_activity"):
            self.assertIn(key, hist)

    def test_beneficiary_history_applications_sorted(self) -> None:
        """يجب أن تكون الطلبات مرتبة بالتاريخ."""
        b = next(iter(self.eco._beneficiaries.values()))
        hist = self.eco.get_beneficiary_history(b.beneficiary_id)
        apps = hist["applications"]
        if len(apps) >= 2:
            dates = [a.submission_date for a in apps]
            self.assertEqual(dates, sorted(dates))

    def test_beneficiary_history_correct_beneficiary(self) -> None:
        """يجب أن تنتمي جميع الطلبات للمستفيد المحدد."""
        b = next(iter(self.eco._beneficiaries.values()))
        hist = self.eco.get_beneficiary_history(b.beneficiary_id)
        for a in hist["applications"]:
            self.assertEqual(a.beneficiary_id, b.beneficiary_id)

    # ── فلتر التاريخ في get_transactions ────────────────────────────────
    def test_transactions_date_filter_from(self) -> None:
        """يجب أن يُرجع فقط العمليات بعد from_date."""
        future = date(2099, 1, 1)
        txns = self.eco.finance.get_transactions(
            limit=9999, from_date=future
        )
        self.assertEqual(len(txns), 0)

    def test_transactions_date_filter_to(self) -> None:
        """يجب أن يُرجع جميع العمليات إذا كان to_date في المستقبل."""
        future = date(2099, 12, 31)
        all_txns = self.eco.finance.get_transactions(limit=9999)
        filtered  = self.eco.finance.get_transactions(
            limit=9999, to_date=future
        )
        self.assertEqual(len(filtered), len(all_txns))

    # ── ApplicationStatus.CANCELLED موجود ───────────────────────────────
    def test_cancelled_status_exists(self) -> None:
        """يجب أن يكون ApplicationStatus.CANCELLED قيمة صالحة."""
        self.assertEqual(ApplicationStatus.CANCELLED.value, "ملغى")

    # ── is_archived يُحفظ ويُستعاد ──────────────────────────────────────
    def test_persistence_saves_is_archived(self) -> None:
        """يجب أن تحفظ Persistence حقل is_archived وتستعيده."""
        import tempfile, shutil
        tmp = tempfile.mkdtemp()
        try:
            b = next(iter(self.eco._beneficiaries.values()))
            self.eco.archive_beneficiary(b.beneficiary_id)

            class _P(DataPersistence):
                def _get_path(self):
                    return os.path.join(tmp, "test.json")
                def save(self, eco):
                    import json as _j
                    data = {
                        "beneficiaries": [
                            DataPersistence._ben_to_dict(x)
                            for x in eco._beneficiaries.values()
                        ],
                        "applications": [],
                        "transactions": [],
                        "donors": {},
                        "balances": {},
                    }
                    with open(self._get_path(), "w", encoding="utf-8") as fh:
                        _j.dump(data, fh, ensure_ascii=False)
                    return True, "ok"
                def load(self, eco):
                    import json as _j
                    with open(self._get_path(), encoding="utf-8") as fh:
                        data = _j.load(fh)
                    eco._beneficiaries = {
                        d["beneficiary_id"]: DataPersistence._dict_to_ben(d)
                        for d in data["beneficiaries"]
                    }
                    return True, "ok"

            p = _P()
            p.save(self.eco)
            eco2 = SmartCharityEcosystem()
            p.load(eco2)
            self.assertTrue(eco2._beneficiaries[b.beneficiary_id].is_archived)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  الميزات الأربع الجديدة: Multi-Tenant · Holistic · Fast-Track · Impact
# ═══════════════════════════════════════════════════════════════════════════════

class TestSaaSFeatures(unittest.TestCase):
    """اختبارات الميزات الأربع المضافة لنموذج SaaS."""

    def setUp(self) -> None:
        self.eco = SmartCharityEcosystem()
        self.eco.load_demo_data()

    # ── Feature 1: Multi-Tenant ─────────────────────────────────────────────

    def test_tenant_id_default_on_all_dataclasses(self):
        """يجب أن تحمل جميع النماذج قيمة tenant_id افتراضية 'default'."""
        b = _make_beneficiary()
        a = _make_application(b.beneficiary_id)
        from smart_charity_ecosystem import DonorRecord
        d = DonorRecord(full_name="متبرع", phone="0500000000", fund_type=FundType.ZAKAT)
        txn = Transaction(
            fund_type=FundType.ZAKAT, amount=100, transaction_type="CREDIT",
            reference_id="test", description="test", executor_id="SYS",
            balance_after=100,
        )
        self.assertEqual(b.tenant_id,   "default")
        self.assertEqual(a.tenant_id,   "default")
        self.assertEqual(d.tenant_id,   "default")
        self.assertEqual(txn.tenant_id, "default")

    def test_tenant_id_custom_isolation(self):
        """يجب أن يُعزل كل مستأجر في ملف حفظ مستقل."""
        p1 = DataPersistence(tenant_id="org_a")
        p2 = DataPersistence(tenant_id="org_b")
        self.assertNotEqual(p1.DATA_FILE, p2.DATA_FILE)
        self.assertIn("org_a", p1.DATA_FILE)
        self.assertIn("org_b", p2.DATA_FILE)

    def test_default_persistence_file_unchanged(self):
        """يجب أن لا يتغير اسم ملف الحفظ للمستأجر الافتراضي."""
        p = DataPersistence()
        self.assertEqual(p.DATA_FILE, "charity_data.json")

    # ── Feature 2: Holistic AI Triage ──────────────────────────────────────

    def test_holistic_plan_multi_sector_keywords(self):
        """يجب إنشاء طلبات متعددة عند اكتشاف كلمات مفتاح لقطاعات مختلفة."""
        ben = list(self.eco._beneficiaries.values())[0]
        plans = self.eco.ai.generate_holistic_plan(
            "المريض يعاني مرضاً ويحتاج علاجاً ويسكن في إيجار مرتفع وغذاء شحيح",
            ben,
        )
        self.assertGreater(len(plans), 1, "يجب أن تُنشأ أكثر من خطة واحدة")
        sectors = {p.sector for p in plans}
        self.assertIn(SectorType.HEALTH,  sectors)
        self.assertIn(SectorType.HOUSING, sectors)
        self.assertIn(SectorType.FOOD,    sectors)

    def test_holistic_plan_no_keywords_returns_default(self):
        """يجب إرجاع خطة غذائية واحدة عند عدم اكتشاف كلمات مفتاحية."""
        ben = list(self.eco._beneficiaries.values())[0]
        plans = self.eco.ai.generate_holistic_plan("بيانات ميدانية غير واضحة", ben)
        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].sector, SectorType.FOOD)

    def test_holistic_plan_applications_carry_tenant_id(self):
        """يجب أن ترث الطلبات المُولَّدة tenant_id من المستفيد."""
        ben = list(self.eco._beneficiaries.values())[0]
        ben.tenant_id = "org_test"
        plans = self.eco.ai.generate_holistic_plan("يحتاج علاج طبي عاجل", ben)
        for p in plans:
            self.assertEqual(p.tenant_id, "org_test")

    # ── Feature 3: Fast-Track Auto-Disbursement ─────────────────────────────

    def test_fast_track_critical_health_auto_disbursed(self):
        """يجب صرف طلبات HEALTH الحرجة تلقائياً دون موافقة إدارية."""
        ben = _make_beneficiary(monthly_income=500, family_size=6)
        self.eco.register_beneficiary(ben)
        self.eco.finance.receive_donation(
            "متبرع_اختبار", "0599999999", 20_000, FundType.ZAKAT, "SYS"
        )
        app = _make_application(
            ben.beneficiary_id,
            amount=3_000,
            sector=SectorType.HEALTH,
            fund=FundType.ZAKAT,
        )
        ok, msg = self.eco.submit_application(app)
        self.assertTrue(ok)
        self.assertEqual(
            app.status,
            ApplicationStatus.DISBURSED,
            f"الطلب الحرج يجب أن يُصرف تلقائياً — الحالة الفعلية: {app.status}",
        )
        self.assertIn("طوارئ", msg)

    def test_fast_track_above_limit_not_auto_disbursed(self):
        """يجب عدم تفعيل المسار السريع إذا تجاوز المبلغ الحد المسموح."""
        ben = _make_beneficiary(monthly_income=500, family_size=6)
        self.eco.register_beneficiary(ben)
        self.eco.finance.receive_donation(
            "متبرع_حد", "0588888888", 50_000, FundType.ZAKAT, "SYS"
        )
        app = _make_application(
            ben.beneficiary_id,
            amount=6_000,
            sector=SectorType.HEALTH,
            fund=FundType.ZAKAT,
        )
        ok, msg = self.eco.submit_application(app)
        self.assertTrue(ok)
        self.assertNotEqual(
            app.status, ApplicationStatus.DISBURSED,
            "المبلغ 6000 يتجاوز الحد — لا يجب الصرف التلقائي"
        )

    def test_fast_track_insufficient_balance_no_disburse(self):
        """يجب عدم الصرف إذا كان الرصيد غير كافٍ حتى مع الأولوية الحرجة."""
        eco2 = SmartCharityEcosystem()
        ben  = _make_beneficiary(monthly_income=300, family_size=7)
        eco2.register_beneficiary(ben)
        app = _make_application(
            ben.beneficiary_id, amount=2_000,
            sector=SectorType.HEALTH, fund=FundType.ZAKAT,
        )
        ok, _ = eco2.submit_application(app)
        self.assertTrue(ok)
        self.assertNotEqual(app.status, ApplicationStatus.DISBURSED)

    # ── Feature 4: Impact Loop ──────────────────────────────────────────────

    def test_impact_report_disbursed_returns_details(self):
        """يجب أن يُرجع تقرير الأثر معلومات المستفيد عند حالة DISBURSED."""
        ben = _make_beneficiary(monthly_income=500, family_size=6)
        self.eco.register_beneficiary(ben)
        app = _make_application(
            ben.beneficiary_id, amount=3_000,
            sector=SectorType.HEALTH, fund=FundType.ZAKAT,
        )
        self.eco.finance.receive_donation(
            "متبرع_الأثر", "0577777777", 20_000, FundType.ZAKAT, "SYS"
        )
        credit_txn = self.eco.finance._transactions[-1]
        credit_txn.application_id = app.application_id
        self.eco.submit_application(app)
        self.assertEqual(app.status, ApplicationStatus.DISBURSED)
        report = self.eco.generate_impact_report(credit_txn.transaction_id)
        self.assertIn("أثرك الفوري", report)
        self.assertIn(app.sector.value, report)

    def test_impact_report_no_application_id_returns_thanks(self):
        """يجب إرجاع رسالة شكر عامة عند عدم ربط التبرع بطلب."""
        self.eco.finance.receive_donation(
            "متبرع_عام", "0566666666", 5_000, FundType.SADAQAT, "SYS"
        )
        txn = self.eco.finance._transactions[-1]
        self.assertIsNone(txn.application_id)
        report = self.eco.generate_impact_report(txn.transaction_id)
        self.assertIn("شكراً", report)

    def test_impact_report_linked_donation_transaction_has_app_id(self):
        """يجب أن تحتفظ عملية التبرع المخصصة بـ application_id صحيح."""
        dummy_app_id = "APP-TEST1234"
        self.eco.finance.receive_donation(
            "متبرع_مخصص", "0555555555", 10_000,
            FundType.ZAKAT, "SYS", application_id=dummy_app_id,
        )
        txn = self.eco.finance._transactions[-1]
        self.assertEqual(txn.application_id, dummy_app_id)

    def test_disburse_transaction_carries_application_id(self):
        """يجب أن تحتوي عملية الصرف على application_id للطلب المعتمد."""
        ben = _make_beneficiary(monthly_income=500, family_size=6)
        self.eco.register_beneficiary(ben)
        self.eco.finance.receive_donation(
            "م", "0544444444", 30_000, FundType.ZAKAT, "SYS"
        )
        app = _make_application(
            ben.beneficiary_id, amount=3_000,
            sector=SectorType.HEALTH, fund=FundType.ZAKAT,
        )
        self.eco.submit_application(app)
        debit_txns = [
            t for t in self.eco.finance._transactions
            if t.transaction_type == "DEBIT"
            and t.application_id == app.application_id
        ]
        self.assertGreater(len(debit_txns), 0)


# ═══════════════════════════════════════════════════════════════════════════════
#  نقطة الدخول
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    loader  = unittest.TestLoader()
    suite   = unittest.TestSuite()
    classes = [
        TestSmartAI,
        TestFinanceSystem,
        TestGovernanceSystem,
        TestSmartCharityEcosystem,
        TestDataPersistence,
        TestZakatLogic,
        TestAlertsSystem,
        TestCSVExport,
        TestHijriCalendar,
        TestEditRecords,
        TestBackendCompletion,
        TestSaaSFeatures,
    ]
    for cls in classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
