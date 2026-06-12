# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 MOCK SOMAFRACTALMEMORY DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════════
# Minimal FastAPI mock for local/standalone development.
# Exposes port 10101.
# ═══════════════════════════════════════════════════════════════════════════════

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic

COPY main.py /app/main.py

EXPOSE 10101

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:10101/api/health/')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10101"]
