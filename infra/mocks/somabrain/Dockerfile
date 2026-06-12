# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 MOCK SOMABRAIN DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════════
# Minimal FastAPI mock for local/standalone development.
# Exposes port 9696.
# ═══════════════════════════════════════════════════════════════════════════════

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn[standard]

COPY main.py /app/main.py

EXPOSE 9696

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9696/api/health/')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9696"]
