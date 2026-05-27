################################################################################
#  Makefile — منظومة العمل الخيري الذكي
#  الاستخدام: make <target>
#  مثال:   make up | make test | make logs
#  ملاحظة: على Windows استخدم Git Bash أو WSL لتشغيل make
################################################################################

.PHONY: help up down build rebuild logs test test-unit test-api \
        install-backend install-frontend-saas frontend-dev backend-dev \
        clean clean-volumes shell-backend shell-frontend

# ── المتغيرات ─────────────────────────────────────────────────────────────────
COMPOSE        = docker-compose
BACKEND_DIR    = backend
FRONTEND_DIR   = frontend-saas
PYTHON         = python
PYTEST         = pytest

# ══════════════════════════════════════════════════════════════════════════════
#  المساعدة
# ══════════════════════════════════════════════════════════════════════════════
help:           ## عرض جميع الأوامر المتاحة
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*##"}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ══════════════════════════════════════════════════════════════════════════════
#  Docker
# ══════════════════════════════════════════════════════════════════════════════
up:             ## تشغيل كل الخدمات في الخلفية (docker-compose up -d)
	$(COMPOSE) up -d

down:           ## إيقاف الخدمات (مع الحفاظ على البيانات)
	$(COMPOSE) down

build:          ## بناء الصور (مع استخدام الـ cache)
	$(COMPOSE) build

rebuild:        ## إعادة بناء الصور من الصفر (بدون cache)
	$(COMPOSE) build --no-cache

restart:        ## إعادة تشغيل الخدمات
	$(COMPOSE) restart

logs:           ## متابعة logs جميع الخدمات
	$(COMPOSE) logs -f

logs-backend:   ## متابعة logs الـ Backend فقط
	$(COMPOSE) logs -f backend

logs-frontend:  ## متابعة logs الـ Frontend فقط
	$(COMPOSE) logs -f frontend

ps:             ## حالة الحاويات
	$(COMPOSE) ps

clean:          ## إيقاف وحذف الحاويات والصور المحلية
	$(COMPOSE) down --rmi local

clean-volumes:  ## ⚠️  إيقاف وحذف كل شيء بما في ذلك البيانات
	$(COMPOSE) down -v --rmi local

shell-backend:  ## فتح shell داخل حاوية الـ Backend
	$(COMPOSE) exec backend /bin/sh

shell-frontend: ## فتح shell داخل حاوية الـ Frontend
	$(COMPOSE) exec frontend /bin/sh

# ══════════════════════════════════════════════════════════════════════════════
#  الاختبارات
# ══════════════════════════════════════════════════════════════════════════════
test: test-unit test-api ## تشغيل جميع الاختبارات

test-unit:      ## اختبارات الوحدة (النواة الأصلية — 95 اختبار)
	PYTHONIOENCODING=utf-8 $(PYTHON) tests.py

test-api:       ## اختبارات التكامل API (Fast-Track + Tenant Isolation)
	cd $(BACKEND_DIR) && $(PYTEST) tests/ -v --tb=short

test-api-ci:    ## اختبارات التكامل (من جذر المشروع — للـ CI)
	PYTHONPATH=. $(PYTEST) $(BACKEND_DIR)/tests/ -v --tb=short

test-coverage:  ## تشغيل الاختبارات مع تقرير التغطية
	cd $(BACKEND_DIR) && $(PYTEST) tests/ -v --tb=short \
		--cov=. --cov-report=term-missing --cov-report=html:coverage_html

# ══════════════════════════════════════════════════════════════════════════════
#  التطوير المحلي (بدون Docker)
# ══════════════════════════════════════════════════════════════════════════════
install-backend: ## تثبيت متطلبات الـ Backend
	pip install -r $(BACKEND_DIR)/requirements.txt
	pip install -r $(BACKEND_DIR)/requirements-dev.txt

install-frontend-saas: ## تثبيت متطلبات الـ Frontend SaaS (يتطلب مسار محلي)
	@echo "انسخ frontend-saas إلى C:\\SmartCharitySaaS أولاً ثم نفّذ: npm install"

backend-dev:    ## تشغيل الـ Backend في وضع التطوير
	cd $(BACKEND_DIR) && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

backend-dev-log: ## تشغيل الـ Backend مع تسجيل مفصّل
	cd $(BACKEND_DIR) && uvicorn main:app --host 0.0.0.0 --port 8000 --reload \
		--log-level debug

# ══════════════════════════════════════════════════════════════════════════════
#  أدوات الجودة
# ══════════════════════════════════════════════════════════════════════════════
lint-backend:   ## فحص الكود بـ ruff (إن كان مثبتاً)
	ruff check $(BACKEND_DIR)/ smart_charity_ecosystem.py || true

format-backend: ## تنسيق الكود بـ black (إن كان مثبتاً)
	black $(BACKEND_DIR)/ smart_charity_ecosystem.py || true

# ══════════════════════════════════════════════════════════════════════════════
#  الإعداد الأولي
# ══════════════════════════════════════════════════════════════════════════════
init:           ## إعداد المشروع للمرة الأولى
	@test -f .env || (cp env.example .env && echo "✓ تم إنشاء .env من env.example — عدّل القيم")
	pip install -r $(BACKEND_DIR)/requirements.txt
	pip install -r $(BACKEND_DIR)/requirements-dev.txt
	@echo ""
	@echo "✓ جاهز! لتشغيل كل شيء: make up"
	@echo "✓ لتشغيل الاختبارات:    make test"
