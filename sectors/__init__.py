"""
حزمة القطاعات التشغيلية الأربعة — Operational Sectors
"""
from .health_sector    import HealthSector
from .housing_sector   import HousingSector
from .recycling_sector import RecyclingSector
from .food_sector      import FoodSector
from smart_charity_ecosystem import BaseSector, SectorType

__all__ = [
    "BaseSector", "SectorType",
    "HealthSector", "HousingSector", "RecyclingSector", "FoodSector",
]
