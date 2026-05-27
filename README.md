# 🌙 منظومة العمل الخيري الذكي
### Smart Charity Ecosystem — v1.0.0

> نظام متكامل لإدارة الزكاة والصدقات والأوقاف بذكاء اصطناعي  
> Python 3.10+ · FastAPI · React 18 · TypeScript · TailwindCSS

---

## 🚀 التشغيل السريع

```bash
# 1. تثبيت المتطلبات
pip install -r requirements.txt

# 2. واجهة سطر الأوامر (CLI)
python main.py

# 3. خادم API (للوحة التحكم)
python main.py --mode api

# 4. اختبارات النظام (82 اختبار)
python main.py --mode test
```

**لوحة التحكم الإلكترونية:**
```bash
# تشغيل Backend
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# تشغيل Frontend
cd C:\SmartCharity && npm run dev   # → http://localhost:5173
```

---

## 📋 نظرة عامة

منظومة متكاملة تجمع بين الفقه الإسلامي في إدارة الزكاة والصدقات والحوكمة المؤسسية الحديثة، مدعومةً بنواة ذكاء اصطناعي تحلّل الأهلية وتحدد الأولويات وتتنبأ بالاحتياجات المستقبلية.

---

## 🏗️ الهيكل المعياري الكامل

```
smart_charity/
├── main.py                  ⚡ نقطة الدخول (CLI / API / Tests)
├── requirements.txt         📦 التبعيات
├── .env                     ⚙️  الإعدادات البيئية
├── core/                    🧠 نواة النظام والذكاء الاصطناعي
│   ├── models.py            — Enums + Dataclasses المشتركة
│   ├── ai_brain.py          — SmartAI (يتعلم · يقترح · يحلل)
│   ├── engine.py            — SmartCharityEcosystem (المحرك)
│   └── database.py          — JSON + SQLite persistence
├── management/              🛡️  إدارة الهياكل والصلاحيات
│   ├── organization.py      — GovernanceSystem + UserRole
│   ├── authority.py         — ApprovalMatrix (مصفوفة الحدود)
│   └── decisions.py         — DecisionEngine (approve/reject/disburse)
├── sectors/                 🏥🏠♻️🍽️ القطاعات التشغيلية
│   ├── health_sector.py     — القطاع الصحي
│   ├── housing_sector.py    — قطاع الإسكان
│   ├── recycling_sector.py  — قطاع التدوير والاستدامة
│   └── food_sector.py       — قطاع الإطعام وحفظ النعمة
├── finance/                 🤲 إدارة الزكاة والمال
│   ├── zakah_system.py      — حساب الزكاة الشرعي (8 أوعية)
│   ├── donations.py         — DonationsManager
│   └── reports.py           — FinanceReporter + KPI
├── utils/                   🔧 أدوات مساعدة
│   ├── logger.py            — Colors · Printer · setup_logger
│   └── alerts.py            — AlertsSystem (6 أنواع تنبيهات)
├── backend/                 🖥️  FastAPI REST API
│   ├── main.py              — 25+ endpoint (single-tenant)
│   ├── saas_api.py          — SaaS Multi-Tenant API (منفذ 8001)
│   └── requirements.txt
├── frontend/                🌐 React 18 + TypeScript
│   └── src/pages/           — 10 صفحات
└── smart_charity_ecosystem.py  📦 النواة الأصلية (4300+ سطر)
```

---

## 🏗️ المعمارية الداخلية (25 كلاس | 100+ دالة)

```
smart_charity_ecosystem.py
│
├── 🎨  Colors + Printer          — ألوان ANSI وطباعة منسّقة
├── 📦  Enums                     — ZakatCategory · FundType · ApplicationStatus
│                                    Priority · UserRole · SectorType
├── 📊  Data Models               — Address · Beneficiary · Application
│                                    Transaction · DonorRecord · KPIReport
│
├── 🧠  SmartAI                   — تحقق الأهلية الشرعية · تسجيل النقاط
│                                    تصنيف الأولويات · التنبؤ بالاحتياجات
│
├── 🛡️  GovernanceSystem          — مصفوفة الصلاحيات · سجل التدقيق
│                                    الموافقات متعددة المستويات · السياسات
│
├── 💰  FinanceSystem             — 4 صناديق منفصلة · إيداع · صرف
│                                    تقارير مالية · سلامة البيانات (SHA-256)
│
├── 🏥🏠♻️🍽️  Sectors (4)           — Health · Housing · Recycling · Food
│
├── 🌐  SmartCharityEcosystem     — المنظوم الرئيسي + بيانات تمثيلية
├── 💾  DataPersistence           — حفظ/تحميل JSON تلقائي
└── 🖥️  CLI                       — 22 خيار تفاعلي في 3 مجموعات
```

---

## ▶️ تشغيل المشروع

### Windows (موصى به)
```cmd
chcp 65001
python smart_charity_ecosystem.py
```

### Linux / macOS
```bash
python3 smart_charity_ecosystem.py
```

> **متطلبات:** Python 3.10+ فقط — لا توجد مكتبات خارجية

---

## 🗺️ دليل القائمة الرئيسية

### 🟢 العمليات التفاعلية
| المفتاح | الوظيفة |
|---------|---------|
| `A` | تسجيل مستفيد جديد + تحقق شرعي فوري |
| `B` | تسجيل تبرع + اختيار الصندوق |
| `C` | تقديم طلب مساعدة + تحليل ذكاء اصطناعي |
| `D` | موافقة / رفض طلب (مع التحقق من الصلاحيات) |
| `E` | صرف أموال طلب معتمد |
| `Z` | **حاسبة الزكاة التفاعلية** (نقود · ذهب · فضة · زراعة · أنعام) |

### 🟣 البيانات
| المفتاح | الوظيفة |
|---------|---------|
| `G` | **لوحة الإحصاء** بمخططات ASCII (حالات · قطاعات · أرصدة · نشاط) |
| `F` | بحث موحّد (اسم / هوية / معرّف / وصف) |
| `S` | حفظ البيانات يدوياً إلى `charity_data.json` |
| `X` | تصدير تقرير شامل إلى ملف `.txt` |

### 🔵 التقارير
| المفتاح | التقرير |
|---------|---------|
| `1` | التقرير الشامل للمنظومة |
| `2` | التقرير المالي التفصيلي |
| `3–6` | قطاعات الصحة / الإسكان / التدوير / الإطعام |
| `7` | سجل التدقيق والحوكمة |
| `8` | ملخص نواة الذكاء الاصطناعي |
| `9` | السياسات والإجراءات المعتمدة |
| `T` | التنبؤ بالاحتياجات المستقبلية (مخطط شريطي) |
| `0` | خروج مع **حفظ تلقائي** |

---

## 💾 الاستمرارية

- عند الخروج (`0`) يُحفظ كل شيء تلقائياً في `charity_data.json`
- عند الفتح مجدداً يُستعاد الوضع السابق تلقائياً
- إن لم يوجد ملف حفظ، تُحمَّل **بيانات تمثيلية** كاملة للتجربة

---

## 🧠 نواة الذكاء الاصطناعي

| الوظيفة | التفاصيل |
|---------|---------|
| تحقق الأهلية | نصاب الزكاة · الدخل الفردي · الوضع الوظيفي · الإعاقة |
| تسجيل النقاط | 0–100 بناءً على 6 عوامل موزونة |
| تحديد الأولوية | CRITICAL / HIGH / MEDIUM / LOW |
| تصنيف المصرف | 8 مصارف شرعية للزكاة |
| التنبؤ | توقع احتياجات الشهر القادم بمعامل نمو 10% |

---

## 💛 حاسبة الزكاة

تحسب الزكاة على الأوعية الشرعية الخمسة:

| الوعاء | النصاب | النسبة |
|--------|--------|--------|
| النقود والأرصدة | 19,500 ريال | 2.5% |
| عروض التجارة | 19,500 ريال | 2.5% |
| الذهب (85 جم) | 19,550 ريال | 2.5% |
| الفضة (595 جم) | 1,785 ريال | 2.5% |
| المحاصيل | 653 كجم × سعر | 5% (مروي) / 10% (غير مروي) |

---

## 🏦 الصناديق المالية المنفصلة

```
الزكاة         ── صارم: فقط للمصارف الثمانية
الصدقات        ── مرن: جميع القطاعات
الأوقاف        ── دائم: ريع فقط
المشاريع المقيدة ── مقيّد: غرض محدد فقط
```

---

## 📁 الملفات المولّدة

| الملف | المحتوى |
|-------|---------|
| `charity_data.json` | بيانات المنظومة (حفظ تلقائي) |
| `charity_report_YYYYMMDD_HHMMSS.txt` | تقارير التصدير |

---

## 👨‍💻 معايير الجودة

- **PEP8** + **Google Python Style Guide**
- توثيق عربي كامل لكل كلاس ودالة
- معالجة استثناءات شاملة
- سلامة البيانات المالية بـ SHA-256
- فصل كامل للمسؤوليات (SRP)
- لا تبعيات خارجية — stdlib فقط

---

---

## 🐳 النشر على الإنتاج (Production Deployment)

> **المتطلبات:** Docker 24+ و Docker Compose v2+

### ⚡ تشغيل المنظومة بأمر واحد

```bash
# 1. انسخ ملف المتغيرات وعدّل القيم
cp env.example .env

# 2. شغّل كل شيء (Backend + Frontend + شبكة مشتركة + Volumes)
docker-compose up -d

# سيتوفر:
#   Backend API  → http://localhost:8000
#   Swagger UI   → http://localhost:8000/docs
#   Frontend SaaS → http://localhost:3000
```

**أوامر مفيدة:**
```bash
docker-compose logs -f backend      # متابعة logs الـ Backend
docker-compose logs -f frontend     # متابعة logs الـ Frontend
docker-compose ps                   # حالة الحاويات
docker-compose down                 # إيقاف مع حفظ البيانات
docker-compose down -v              # إيقاف وحذف البيانات
docker-compose build --no-cache     # إعادة بناء الصور من الصفر
```

---

### 🗄️ إعداد Supabase (اختياري)

البيانات تُحفَظ بـ **JSON** افتراضياً. لتفعيل Supabase:

1. أنشئ مشروعاً على [supabase.com](https://supabase.com)
2. في **SQL Editor** نفِّذ:

```sql
-- جدول المستفيدين
CREATE TABLE beneficiaries (
    id            TEXT PRIMARY KEY,
    tenant_id     TEXT NOT NULL,
    full_name     TEXT,
    national_id   TEXT UNIQUE,
    phone         TEXT,
    city          TEXT,
    monthly_income FLOAT,
    family_size   INT,
    is_eligible   BOOLEAN,
    created_at    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_ben_tenant ON beneficiaries (tenant_id);

-- جدول الطلبات
CREATE TABLE applications (
    id                TEXT PRIMARY KEY,
    tenant_id         TEXT NOT NULL,
    beneficiary_id    TEXT,
    sector            TEXT,
    fund_type         TEXT,
    status            TEXT,
    priority          TEXT,
    requested_amount  FLOAT,
    approved_amount   FLOAT DEFAULT 0,
    ai_score          FLOAT DEFAULT 0,
    created_at        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_app_tenant ON applications (tenant_id);

-- Row Level Security (عزل المستأجرين على مستوى قاعدة البيانات)
ALTER TABLE beneficiaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications   ENABLE ROW LEVEL SECURITY;
```

3. أضف بياناته في `.env`:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

---

### 🔐 متغيرات البيئة (Environment Variables)

| المتغير | الوصف | مطلوب |
|---------|-------|-------|
| `JWT_SECRET_KEY` | مفتاح تشفير JWT (32+ حرف عشوائي) | **نعم** |
| `TOKEN_EXPIRE_HOURS` | مدة صلاحية التوكن بالساعات (افتراضي: 24) | لا |
| `SUPABASE_URL` | رابط مشروع Supabase | لا* |
| `SUPABASE_SERVICE_KEY` | مفتاح الخدمة من Supabase | لا* |
| `ALLOWED_ORIGINS` | نطاقات CORS مفصولة بفاصلة | لا |
| `BACKEND_URL` | رابط الـ Backend الداخلي لـ Next.js | لا |
| `NEXT_PUBLIC_API_URL` | رابط الـ API للمتصفح | لا |

> \* عند غياب Supabase تتراجع المنظومة إلى JSON محلي تلقائياً.

**توليد مفتاح JWT عشوائي:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### 🧪 تشغيل الاختبارات

```bash
# 1. اختبارات الوحدة (النواة الأصلية — 95 اختبار)
python tests.py

# 2. اختبارات التكامل API (fast-track + tenant isolation)
cd backend
pip install -r requirements-dev.txt
pytest tests/ -v

# 3. كلاهما معاً (CI style)
pytest backend/tests/ -v && python tests.py
```

---

### 🔄 خط أنابيب CI/CD

الملف `.github/workflows/ci-cd.yml` يُشغِّل تلقائياً عند كل `push` على `main`:

```
push to main
    │
    ├── 🐍 backend-tests    → pytest (unit + integration)
    ├── ⚡ frontend-build   → npm lint + npm build
    │
    └── 🐳 docker-push (بعد نجاح الاختبارين)
            ├── Build & Push scs-backend:latest
            └── Build & Push scs-frontend:latest
```

**Secrets المطلوبة في GitHub:**
| Secret | الوصف |
|--------|-------|
| `DOCKERHUB_USERNAME` | اسم حساب Docker Hub |
| `DOCKERHUB_TOKEN` | Access Token من Docker Hub |

---

### 🗂️ هيكل المشروع (النسخة الكاملة)

```
Smart Charity Ecosystem/
├── smart_charity_ecosystem.py   📦 النواة (~4550 سطر)
├── tests.py                     🧪 95 اختبار وحدة
├── main.py                      ⚡ نقطة دخول CLI/API/Tests
├── docker-compose.yml           🐳 تشغيل كل شيء بأمر واحد
├── env.example                  ⚙️  نموذج متغيرات البيئة
├── backend/
│   ├── Dockerfile               🐳 multi-stage (context=root)
│   ├── main.py                  🖥️  FastAPI (25+ endpoint legacy)
│   ├── schemas.py               📋 Pydantic models
│   ├── core.py                  🏢 Tenant Registry
│   ├── requirements.txt
│   ├── requirements-dev.txt     🧪 pytest + httpx
│   ├── pytest.ini
│   ├── api/
│   │   ├── deps.py              🔑 JWT dependency
│   │   └── v1/
│   │       ├── auth.py          → POST /auth/login
│   │       ├── beneficiaries.py → GET/POST /beneficiaries
│   │       ├── applications.py  → POST /applications/submit
│   │       └── donations.py     → POST /donations + impact-report
│   ├── db/
│   │   └── supabase_client.py   🗄️  Supabase persistence
│   └── tests/
│       ├── conftest.py          🔧 fixtures + JWT helpers
│       └── test_api_integration.py  🧪 10 integration tests
├── frontend-saas/               ⚡ Next.js 14 SaaS
│   ├── Dockerfile               🐳 multi-stage standalone
│   ├── next.config.mjs
│   ├── app/
│   │   ├── login/page.tsx       🔐 تسجيل الدخول
│   │   ├── admin/               👔 لوحة الإدارة
│   │   │   ├── page.tsx         → Dashboard
│   │   │   └── impact/page.tsx  → تقارير الأثر
│   │   └── field-worker/        📱 واجهة ميدانية mobile-first
│   ├── components/
│   │   ├── sidebar.tsx
│   │   ├── impact-card.tsx
│   │   └── providers.tsx
│   ├── lib/
│   │   ├── api.ts               🌐 Axios client
│   │   └── auth.ts              🔑 Cookie session helpers
│   └── middleware.ts            🛡️  Role-based routing
├── frontend/                    🌐 React 18 legacy (port 5173)
└── .github/
    └── workflows/
        └── ci-cd.yml            🔄 CI/CD Pipeline
```

---

*جعله الله في ميزان حسناتكم* 🌙
