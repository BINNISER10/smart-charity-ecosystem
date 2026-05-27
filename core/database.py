"""
إدارة قاعدة البيانات — Database Manager
=========================================
يدعم وضعَي التخزين:
  ① JSON  (الافتراضي — بدون إعداد إضافي)
  ② SQLite (ملف محلي دائم، أسرع وأكثر موثوقية)

الاستخدام::

    from core.database import DataPersistence, get_db

    # JSON (الافتراضي)
    db = DataPersistence()
    db.save(eco)

    # SQLite
    db = DataPersistence(backend="sqlite", path="charity.db")
    db.save(eco)
"""

from __future__ import annotations
import json
import sqlite3
import os
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional, Tuple

from smart_charity_ecosystem import DataPersistence, HijriCalendar

if TYPE_CHECKING:
    from smart_charity_ecosystem import SmartCharityEcosystem


# ── SQLite backend (إضافي) ────────────────────────────────────────────────────

class SQLitePersistence:
    """
    طبقة حفظ البيانات باستخدام SQLite.

    تحفظ snapshot كامل (JSON blob) داخل جدول SQLite بدلاً من ملف JSON.
    يمكن توسيعها لاحقاً لـ PostgreSQL بتغيير connection string فقط.
    """

    TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS snapshots (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        saved_at    TEXT    NOT NULL,
        data        TEXT    NOT NULL
    );
    CREATE TABLE IF NOT EXISTS audit_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at   TEXT    NOT NULL,
        actor       TEXT    NOT NULL,
        action      TEXT    NOT NULL,
        details     TEXT
    );
    """

    def __init__(self, db_path: str = "charity.db") -> None:
        self._path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self._path) as conn:
            conn.executescript(self.TABLE_DDL)

    def save(self, eco: "SmartCharityEcosystem") -> Tuple[bool, str]:
        """حفظ snapshot كامل في SQLite."""
        try:
            from smart_charity_ecosystem import FundType, SmartCharityEcosystem as _Eco
            dp = DataPersistence()
            snapshot = {
                "version":       _Eco.VERSION,
                "saved_at":      datetime.now().isoformat(),
                "beneficiaries": [dp._ben_to_dict(b) for b in eco._beneficiaries.values()],
                "applications":  [dp._app_to_dict(a) for a in eco._all_applications.values()],
                "transactions":  [dp._txn_to_dict(t) for t in eco.finance._transactions],
                "balances":      {ft.value: eco.finance._balances[ft] for ft in FundType},
                "donors":        [
                    {
                        "donor_id":       d.donor_id,
                        "full_name":      d.full_name,
                        "phone":          d.phone,
                        "fund_type":      d.fund_type.value,
                        "total_donated":  d.total_donated,
                        "donation_count": d.donation_count,
                    }
                    for d in eco.finance._donors.values()
                ],
            }
            blob = json.dumps(snapshot, ensure_ascii=False, default=str)
            ts   = datetime.now().isoformat()
            with sqlite3.connect(self._path) as conn:
                conn.execute(
                    "INSERT INTO snapshots (saved_at, data) VALUES (?, ?)",
                    (ts, blob),
                )
            return True, f"تم الحفظ في SQLite بنجاح [{ts[:19]}]"
        except Exception as exc:
            return False, f"خطأ في الحفظ: {exc}"

    def load(self, eco: "SmartCharityEcosystem") -> Tuple[bool, str]:
        """تحميل آخر snapshot من SQLite (عبر ملف JSON مؤقت)."""
        try:
            with sqlite3.connect(self._path) as conn:
                row = conn.execute(
                    "SELECT data FROM snapshots ORDER BY id DESC LIMIT 1"
                ).fetchone()
            if not row:
                return False, "لا توجد بيانات محفوظة في SQLite"
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as f:
                f.write(row[0])
                tmp_path = f.name
            try:
                dp = DataPersistence()
                original = dp.DATA_FILE
                dp.DATA_FILE = tmp_path
                result = dp.load(eco)
                dp.DATA_FILE = original
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            return result
        except Exception as exc:
            return False, f"خطأ في التحميل: {exc}"


def get_db(backend: str = "json", path: Optional[str] = None) -> object:
    """
    مصنع طبقة التخزين — يُرجع الـ backend المطلوب.

    المعاملات:
        backend : "json" | "sqlite"
        path    : مسار الملف (اختياري)

    المخرجات:
        DataPersistence أو SQLitePersistence
    """
    if backend == "sqlite":
        return SQLitePersistence(path or "charity.db")
    return DataPersistence(path or "charity_data.json")


__all__ = ["DataPersistence", "HijriCalendar", "SQLitePersistence", "get_db"]
