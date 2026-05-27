"""
نواة المنظومة الخيرية الذكية — Core Package
"""
from .models import (
    ZakatCategory, FundType, ApplicationStatus, Priority,
    UserRole, SectorType, Address, Beneficiary, Application,
    Transaction, DonorRecord, KPIReport,
)
from .ai_brain  import SmartAI
from .engine    import SmartCharityEcosystem
from .database  import DataPersistence, HijriCalendar

__all__ = [
    "ZakatCategory", "FundType", "ApplicationStatus", "Priority",
    "UserRole", "SectorType", "Address", "Beneficiary", "Application",
    "Transaction", "DonorRecord", "KPIReport",
    "SmartAI", "SmartCharityEcosystem", "DataPersistence", "HijriCalendar",
]
