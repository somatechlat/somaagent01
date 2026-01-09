# ═══════════════════════════════════════════════════════════════════════════════
# 🐳 SOMA STACK SAAS DOCKERFILE
# ═══════════════════════════════════════════════════════════════════════════════
# This image combines SomaBrain, FractalMemory, and Agent01 into a SINGLE
# deployment unit. Usage of `supervisord` manages the internal processes.
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 1: RUST BUILDER (SomaBrain Core)
# ═══════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS rust-builder
WORKDIR /rust

# Install Rust toolchain
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain=1.83.0
ENV PATH="/root/.cargo/bin:${PATH}"
RUN pip install maturin

# Copy Rust source from SomaBrain context (Assumed context is root of MONOREPO logic, 
# but here we copy from the specific relative paths mapped in docker-compose context)
COPY somabrain/rust_core /rust/rust_core
WORKDIR /rust/rust_core
RUN maturin build --release -o /rust/dist

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 2: PYTHON BUILDER (Dependencies)
# ═══════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=0
WORKDIR /build

# Copy Requirements
COPY somaAgent01/requirements.txt /build/req_agent.txt
COPY somabrain/pyproject.toml /build/somabrain_pyproject.toml
COPY somafractalmemory/api-requirements.txt /build/req_memory.txt

# Copy Rust Wheel
COPY --from=rust-builder /rust/dist /build/wheels

# Install Build Tools
RUN pip install --upgrade pip build setuptools wheel

# Install Requirements (Order matters for constraints)
RUN pip install -r req_agent.txt
RUN pip install -r req_memory.txt
# Install Rust Wheel
RUN pip install /build/wheels/*.whl
# Install additional dependencies for Brain (from pyproject implied)
RUN pip install "PyJWT[crypto]" confluent-kafka kafka-python python-snappy six pydantic-settings gunicorn fastavro

# ═══════════════════════════════════════════════════════════════════════════════
# STAGE 3: RUNTIME (The SaaS Stack)
# ═══════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# System Deps (Supervisor, Netcat for wait-for, curl for health)
RUN apt-get update && apt-get install -y --no-install-recommends \
    supervisor \
    netcat-openbsd \
    curl \
    python3-numpy \
    && rm -rf /var/lib/apt/lists/*

# Copy Installed Packages from Builder
COPY --from=python-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# ---------------------------------------------------------------------------
# COPY SOURCE CODE (All 3 Repos)
# ---------------------------------------------------------------------------
# Note: Docker Compose build context must be set effectively to allow this.
# We assume the build context is the PARENT directory containing all 3 repos,
# OR we rely on the `somaAgent01` repo having copied them? 
# NO - The USER said "somaAgent01" is the repo. 
# WE MUST ASSUME the user will build this with a context that has access to all 3.
# Or better: We assume the standard layout where directories are siblings.
# But Dockerfile CANNOT step out of context.
#
# STRATEGY: We will assume the Build Context is set to the PARENT folder of the 3 repos.
# ---------------------------------------------------------------------------

COPY somaAgent01 /app/somaAgent01
COPY somabrain /app/somabrain
COPY somafractalmemory /app/somafractalmemory

# Organization: Move them to root or keep structure?
# To simplify imports like `import somabrain`, we need them on PYTHONPATH.
# Since they are folders inside /app, we set PYTHONPATH.

ENV PYTHONPATH=/app/somaAgent01:/app/somabrain:/app/somafractalmemory:/app:$PYTHONPATH

# ---------------------------------------------------------------------------
# CONFIGURATION & SCRIPTS
# ---------------------------------------------------------------------------
COPY somaAgent01/infra/saas_deployment/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY somaAgent01/infra/saas_deployment/start_saas.sh /app/start_saas.sh

# Create Helper Management Scripts
# (Symlinks to manage.py in respective folders)
RUN ln -s /app/somabrain/manage.py /app/manage_brain.py
RUN ln -s /app/somafractalmemory/manage.py /app/manage_memory.py
RUN ln -s /app/somaAgent01/manage.py /app/manage_agent.py

# Permissions
RUN chmod +x /app/start_saas.sh
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ---------------------------------------------------------------------------
# EXPOSE PORTS (639xx Range Mapping happen in Compose)
# ---------------------------------------------------------------------------
# Internal Ports
EXPOSE 9000 9696 10101

# ---------------------------------------------------------------------------
# STARTUP
# ---------------------------------------------------------------------------
ENTRYPOINT ["/app/start_saas.sh"]
