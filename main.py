"""
الملف الرئيسي لتشغيل المنظومة — Smart Charity Ecosystem Entry Point
====================================================================
أوضاع التشغيل:

  ① واجهة سطر الأوامر (CLI) — التفاعل المباشر:
      python main.py
      python main.py --mode cli

  ② خادم الـ API (Backend) — للوحة التحكم الإلكترونية:
      python main.py --mode api
      python main.py --mode api --host 0.0.0.0 --port 8000

  ③ اختبارات النظام — التحقق من سلامة المنظومة:
      python main.py --mode test
"""

import argparse
import sys
import os

# إضافة مجلد المشروع لمسار Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_cli() -> None:
    """تشغيل واجهة سطر الأوامر التفاعلية."""
    from smart_charity_ecosystem import CLI, SmartCharityEcosystem, DataPersistence
    eco = SmartCharityEcosystem()
    persistence = DataPersistence()
    persistence.load(eco)
    cli = CLI(eco, persistence)
    cli.run()


def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = True) -> None:
    """تشغيل خادم FastAPI (Single-Tenant)."""
    try:
        import uvicorn
        uvicorn.run(
            "backend.main:app",
            host=host,
            port=port,
            reload=reload,
        )
    except ImportError:
        print("❌ uvicorn غير مثبت. نفّذ: pip install uvicorn[standard]")
        sys.exit(1)


def run_saas(host: str = "0.0.0.0", port: int = 8001, reload: bool = True) -> None:
    """تشغيل SaaS Multi-Tenant API على منفذ 8001."""
    try:
        import uvicorn
        uvicorn.run(
            "backend.saas_api:saas_app",
            host=host,
            port=port,
            reload=reload,
        )
    except ImportError:
        print("❌ uvicorn غير مثبت. نفّذ: pip install uvicorn[standard]")
        sys.exit(1)


def run_tests() -> None:
    """تشغيل مجموعة الاختبارات."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "tests.py"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(result.returncode)


def show_structure() -> None:
    """عرض الهيكل التنظيمي للمنظومة."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║          منظومة العمل الخيري الذكي — v1.0.0                   ║
╠══════════════════════════════════════════════════════════════════╣
║  smart_charity/                                                  ║
║  ├── main.py              ⚡ نقطة الدخول الرئيسية              ║
║  ├── requirements.txt     📦 المكتبات المطلوبة                  ║
║  ├── .env                 ⚙️  الإعدادات البيئية                 ║
║  ├── core/                🧠 نواة النظام والذكاء الاصطناعي       ║
║  │   ├── models.py        — النماذج والأنواع المشتركة           ║
║  │   ├── ai_brain.py      — العقل الذكي (يتعلم-يقترح-يحلل)    ║
║  │   ├── engine.py        — المحرك الرئيسي للمنظومة             ║
║  │   └── database.py      — قاعدة البيانات (JSON/SQLite)        ║
║  ├── management/          🛡️  إدارة الهياكل والصلاحيات          ║
║  │   ├── organization.py  — الهيكل التنظيمي والأدوار            ║
║  │   ├── authority.py     — مصفوفة الصلاحيات والتوكيل          ║
║  │   └── decisions.py     — نظام القرارات والتعميد              ║
║  ├── sectors/             🏥🏠♻️🍽️ القطاعات التشغيلية           ║
║  │   ├── health_sector.py   — القطاع الصحي                     ║
║  │   ├── housing_sector.py  — قطاع الإسكان                     ║
║  │   ├── recycling_sector.py— قطاع التدوير والاستدامة           ║
║  │   └── food_sector.py     — قطاع الإطعام وحفظ النعمة         ║
║  ├── finance/             🤲 إدارة الزكاة والمال والتبرعات      ║
║  │   ├── zakah_system.py  — نظام الزكاة الشرعي والمالي          ║
║  │   ├── donations.py     — إدارة الصدقات والتبرعات             ║
║  │   └── reports.py       — التقارير المالية والشرعية           ║
║  ├── utils/               🔧 أدوات مساعدة                      ║
║  │   ├── logger.py        — نظام التسجيل والمتابعة              ║
║  │   └── alerts.py        — نظام التنبيهات الذكي               ║
║  ├── backend/             🖥️  FastAPI REST API                   ║
║  │   ├── main.py          — 25+ endpoint (Single-Tenant, :8000) ║
║  │   └── saas_api.py      — SaaS Multi-Tenant API (:8001)       ║
║  └── frontend/            🌐 React 18 + TypeScript (Vite)       ║
║      └── src/pages/       — 10 صفحات (Dashboard→Donors)        ║
╚══════════════════════════════════════════════════════════════════╝
    """)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="منظومة العمل الخيري الذكي",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  python main.py                        # CLI تفاعلي
  python main.py --mode api             # خادم API
  python main.py --mode api --port 9000 # API على منفذ مختلف
  python main.py --mode test            # اختبارات النظام
  python main.py --mode saas            # SaaS API (منفذ 8001)
  python main.py --structure            # عرض هيكل المشروع
        """,
    )
    parser.add_argument("--mode", choices=["cli", "api", "saas", "test"], default="cli")
    parser.add_argument("--host",   default="0.0.0.0")
    parser.add_argument("--port",   type=int, default=None, help="المنفذ (افتراضي: 8000 لـ api، 8001 لـ saas)")
    parser.add_argument("--reload", action="store_true", default=True)
    parser.add_argument("--structure", action="store_true", help="عرض هيكل المشروع")

    args = parser.parse_args()

    if args.structure:
        show_structure()
        return

    if args.mode == "cli":
        run_cli()
    elif args.mode == "api":
        run_api(args.host, args.port or 8000, args.reload)
    elif args.mode == "saas":
        run_saas(args.host, args.port or 8001, args.reload)
    elif args.mode == "test":
        run_tests()


if __name__ == "__main__":
    # chcp 65001 لدعم العربية في Windows
    if sys.platform == "win32":
        import subprocess
        subprocess.run("chcp 65001 >nul 2>&1", shell=True)
    main()
