"""
نظام الزكاة الشرعي والمالي — Zakah System
==========================================
يُطبّق أحكام الزكاة وفق الفقه الإسلامي:

أولاً — الأصناف الثمانية (التوبة: 60):
  ① الفقراء    ② المساكين   ③ العاملون عليها  ④ المؤلفة قلوبهم
  ⑤ الرقاب     ⑥ الغارمون  ⑦ في سبيل الله   ⑧ ابن السبيل

ثانياً — حساب الزكاة:
  ┌────────────────┬──────────────────┬────────────┐
  │ الوعاء        │ النصاب           │ الواجب    │
  ├────────────────┼──────────────────┼────────────┤
  │ النقود         │ 85 جرام ذهب     │ 2.5 %     │
  │ عروض التجارة  │ مثل النقود       │ 2.5 %     │
  │ الذهب والفضة  │ 85 / 595 جرام   │ 2.5 %     │
  │ الزروع        │ 653 كجم          │ 5% / 10%  │
  │ الأسهم        │ مثل النقود       │ 2.5 %     │
  │ صناديق الاست. │ على الأرباح      │ 2.5 %     │
  │ العقارات      │ على الإيجار      │ 2.5 %     │
  │ المواشي       │ حسب النوع        │ متفاوت    │
  └────────────────┴──────────────────┴────────────┘

ثالثاً — شروط الأهلية:
  «لا يُصرف لغني ولا لقوي مكتسب»
  - الدخل الفردي < {MAX_ELIGIBLE_INCOME_PER_CAPITA} ريال/شهر
  - لا يملك نصاباً (> {NISAB_THRESHOLD} ريال)
"""

from __future__ import annotations
from typing import Dict, Any

from smart_charity_ecosystem import SmartAI, ZakatCategory

# ── ثوابت الزكاة ─────────────────────────────────────────────────────────────
NISAB_THRESHOLD                = 5_000.0    # ريال (تقريباً 85 جرام ذهب)
MAX_ELIGIBLE_INCOME_PER_CAPITA = 2_500.0    # ريال/شهر للفرد
ZAKAT_RATE                     = 0.025      # 2.5 %
GOLD_PRICE_PER_GRAM            = 220.0      # ريال / جرام (تقريبي)
SILVER_PRICE_PER_GRAM          = 3.0        # ريال / جرام (تقريبي)
SILVER_NISAB_GRAMS             = 595.0      # جرام


class ZakahSystem:
    """
    نظام حساب الزكاة الشرعي.

    الاستخدام::

        zs = ZakahSystem()

        # حساب زكاة شاملة
        result = zs.calculate(
            cash=50_000,
            trade_goods=30_000,
            gold_grams=100,
        )
        print(result["total_zakat"])

        # تصنيف المستفيد
        category = zs.classify_recipient(income=800, family_size=5)
    """

    def __init__(self) -> None:
        self._ai = SmartAI()

    def calculate(
        self,
        cash: float          = 0.0,
        trade_goods: float   = 0.0,
        gold_grams: float    = 0.0,
        silver_grams: float  = 0.0,
        stocks: float        = 0.0,
        investments: float   = 0.0,
        real_estate: float   = 0.0,
        livestock: float     = 0.0,
    ) -> Dict[str, Any]:
        """
        حساب زكاة شامل لجميع أوعية الزكاة.

        المخرجات:
            قاموس يحتوي على:
              - total_zakatable : إجمالي المال الزكوي
              - total_zakat     : مقدار الزكاة الواجبة
              - is_above_nisab  : هل يبلغ النصاب؟
              - breakdown       : تفصيل كل وعاء
        """
        gold_val   = gold_grams   * GOLD_PRICE_PER_GRAM
        silver_val = silver_grams * SILVER_PRICE_PER_GRAM

        breakdown = {
            "النقود":          cash,
            "عروض التجارة":    trade_goods,
            "الذهب":           gold_val,
            "الفضة":           silver_val,
            "الأسهم":          stocks,
            "صناديق الاستثمار": investments,
            "العقارات":        real_estate,
            "المواشي":         livestock,
        }

        total_zakatable = sum(breakdown.values())
        is_above_nisab  = total_zakatable >= NISAB_THRESHOLD
        total_zakat     = total_zakatable * ZAKAT_RATE if is_above_nisab else 0.0

        return {
            "total_zakatable": total_zakatable,
            "total_zakat":     total_zakat,
            "is_above_nisab":  is_above_nisab,
            "nisab_threshold": NISAB_THRESHOLD,
            "zakat_rate":      ZAKAT_RATE,
            "breakdown":       breakdown,
        }

    def classify_recipient(
        self,
        monthly_income: float,
        family_size: int = 1,
        has_disability: bool = False,
    ) -> ZakatCategory | None:
        """
        تصنيف المستفيد في الصنف الزكوي المناسب.

        المخرجات:
            ZakatCategory أو None إذا لم يستحق
        """
        income_per_capita = monthly_income / max(family_size, 1)
        if income_per_capita < MAX_ELIGIBLE_INCOME_PER_CAPITA * 0.5:
            return ZakatCategory.FUQARA
        if income_per_capita < MAX_ELIGIBLE_INCOME_PER_CAPITA:
            return ZakatCategory.MASAKIN
        if has_disability:
            return ZakatCategory.GHARIMUN
        return None


__all__ = ["ZakahSystem", "ZakatCategory", "NISAB_THRESHOLD", "ZAKAT_RATE"]
