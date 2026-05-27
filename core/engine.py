"""
محرك القواعد الشرعية والنظامية — Rules & Orchestration Engine
==============================================================
المنظومة الرئيسية التي تربط وتنسّق جميع المكونات:

  SmartCharityEcosystem
  ├── ai          → SmartAI         (core/ai_brain.py)
  ├── governance  → GovernanceSystem (management/)
  ├── finance     → FinanceSystem    (finance/)
  └── sectors     → {Health, Housing, Recycling, Food}Sector (sectors/)

المسؤوليات:
  - تسجيل المستفيدين والتحقق من أهليتهم
  - تقديم الطلبات وتحليلها ذكياً
  - معالجة الموافقات وصرف المستحقات
  - توليد التقارير الشاملة
  - أرشفة الحالات واستعادتها
"""

from smart_charity_ecosystem import SmartCharityEcosystem

__all__ = ["SmartCharityEcosystem"]
