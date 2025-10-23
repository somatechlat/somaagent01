# Production-ready Dockerfile with all dependencies
FROM python:3.12-slim

ENV PYTHONPATH=/git/agent-zero
ENV PATH="/opt/venv-a0/bin:${PATH}"
WORKDIR /git/agent-zero

# Copy application files
COPY ./run_ui.py ./agent.py ./models.py ./initialize.py ./preload.py ./prepare.py /git/agent-zero/
COPY ./python/ /git/agent-zero/python/
COPY ./services/ /git/agent-zero/services/
COPY ./common/ /git/agent-zero/common/
COPY ./conf/ /git/agent-zero/conf/
COPY ./prompts/ /git/agent-zero/prompts/
COPY ./webui/ /git/agent-zero/webui/

# Install required dependencies (trimmed)
RUN apt-get update && apt-get install -y --no-install-recommends \
                build-essential \
                git \
                cmake \
                libopenblas-dev \
                libomp-dev \
        && rm -rf /var/lib/apt/lists/* \
        && python3 -m venv /opt/venv-a0 \
        && /opt/venv-a0/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
        && /opt/venv-a0/bin/pip install --no-cache-dir \
        fastapi==0.115.2 \
        uvicorn==0.32.0 \
        fasta2a==0.5.0 \
        fastmcp==2.3.4 \
        mcp==1.13.1 \
        python-dotenv==1.1.0 \
        Flask==3.1.2 \
        PyYAML==6.0.3 \
        httpx==0.28.1 \
        redis==6.4.0 \
        aiokafka==0.11.0 \
        langchain-core==0.1.53 \
        python-crontab==2.7.1 \
        psycopg[binary]==3.2.3 \
        grpcio==1.67.1 \
        protobuf==5.27.3 \
        aiohttp==3.13.1 \
        asyncpg==0.30.0 \
        a2wsgi==1.10.10 \
        opentelemetry-api==1.29.0 \
        opentelemetry-sdk==1.29.0 \
        opentelemetry-instrumentation==0.50b0 \
        opentelemetry-instrumentation-fastapi==0.50b0 \
        opentelemetry-instrumentation-httpx==0.50b0 \
        prometheus-client==0.21.0 \
        webcolors==24.11.1 \
        nest-asyncio==1.6.0 \
        pybreaker==1.1.0 \
        regex==2024.9.11 \
        pytz==2024.2 \
        # Ensure runtime crypto, HF hub and pydantic compatibility are present
        cryptography==46.0.3 \
        "huggingface-hub==0.13.3" \
        pathspec==0.10.3 \
        pydantic==2.11.0 \
        PyJWT==2.8.0

# Heavy ML deps for local embeddings and FAISS
RUN /opt/venv-a0/bin/pip install --no-cache-dir \
        "openai>=1.99.5,<3" \
        litellm==1.78.6 \
        sentence-transformers==2.2.2 \
        transformers \
        faiss-cpu \
        langchain-community \
        langchain \
        # Install CPU wheels for torch from the official PyTorch CPU index
        --extra-index-url https://download.pytorch.org/whl/cpu \
        torch torchvision torchaudio

EXPOSE 80 8010 20017
CMD ["/opt/venv-a0/bin/python", "run_ui.py", "--host=0.0.0.0", "--port=80"]
