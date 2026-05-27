"""
نظام التسجيل والمتابعة — Logger & Display Utilities
=====================================================
يوفر:
  - Colors   : ألوان ANSI لواجهة CLI
  - Printer  : طباعة منسّقة بالعربية
  - HijriCalendar : تحويل التاريخ بين الميلادي والهجري
  - setup_logger  : إعداد نظام التسجيل (logging)
"""

import logging
import pathlib
from smart_charity_ecosystem import Colors, Printer, HijriCalendar

_LOGS_DIR = pathlib.Path(__file__).resolve().parent.parent / "logs"
_LOGS_DIR.mkdir(exist_ok=True)


def setup_logger(name: str = "SmartCharity", level: int = logging.INFO) -> logging.Logger:
    """
    إعداد وإرجاع مسجّل (logger) موحّد للمنظومة.

    المعاملات:
        name  : اسم المسجّل.
        level : مستوى التسجيل (INFO, DEBUG, WARNING, ERROR).

    المخرجات:
        logging.Logger : كائن المسجّل الجاهز للاستخدام.
    """
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(name)
    if not logger.handlers:
        # معالج الطرفية
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(fmt)
        logger.addHandler(stream_handler)

        # معالج ملف العمليات (INFO+)
        ops_handler = logging.FileHandler(
            _LOGS_DIR / "operations.log", encoding="utf-8"
        )
        ops_handler.setFormatter(fmt)
        ops_handler.setLevel(logging.INFO)
        logger.addHandler(ops_handler)

        # معالج ملف الأخطاء (WARNING+)
        err_handler = logging.FileHandler(
            _LOGS_DIR / "errors.log", encoding="utf-8"
        )
        err_handler.setFormatter(fmt)
        err_handler.setLevel(logging.WARNING)
        logger.addHandler(err_handler)

    logger.setLevel(level)
    return logger


__all__ = ["Colors", "Printer", "HijriCalendar", "setup_logger"]
