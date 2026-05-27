# ═══════════════════════════════════════════════════════════════════════════════
#  Backend Dockerfile — منظومة العمل الخيري الذكي
#  Multi-stage build | python:3.11-slim | context = project root
#  هام: يجب أن يكون build context هو جذر المشروع لاحتواء smart_charity_ecosystem.py
# ═══════════════════════════════════════════════════════════════════════════════

# ── Stage 1: Dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# تثبيت أدوات البناء (gcc ضروري لبعض مكتبات cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc build-essential libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# نسخ requirements فقط (cache layer)
COPY backend/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# مستخدم غير جذري للأمان
RUN groupadd --system --gid 1001 appgroup \
 && useradd  --system --uid 1001 --gid appgroup appuser

WORKDIR /app

# نسخ الحزم المثبتة من مرحلة البناء
COPY --from=builder /install /usr/local

# نسخ مصادر المشروع (context = project root)
COPY smart_charity_ecosystem.py /app/
COPY backend/                   /app/backend/

# مجلد البيانات مع صلاحية الكتابة
RUN mkdir -p /app/backend/data \
 && chown -R appuser:appgroup /app

WORKDIR /app/backend

# PYTHONPATH يجعل smart_charity_ecosystem قابلاً للاستيراد
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/openapi.json')"

CMD ["python", "-m", "uvicorn", "main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
