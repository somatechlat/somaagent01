#!/bin/bash
set -euo pipefail

# VIBE CODING RULES COMPLIANT DEPLOYMENT SCRIPT
# Real implementations only - no placeholders, no fake deployments

echo "🚀 Starting SomaAgent01 FastA2A Development Deployment"
echo "========================================================"

# Step 1: Validate environment
echo "📋 Step 1: Validating environment..."
if [ ! -f ".env" ]; then
    echo "❌ ERROR: .env file not found. Please create it with required variables."
    exit 1
fi

# Step 2: Clean up any existing containers
echo "🧹 Step 2: Cleaning up existing containers..."
make dev-down-clean 2>/dev/null || true

# Step 3: Ensure Docker networks exist
echo "🌐 Step 3: Ensuring Docker networks exist..."
docker network inspect somaagent01 >/dev/null 2>&1 || docker network create somaagent01
docker network inspect somaagent01_dev >/dev/null 2>&1 || docker network create somaagent01_dev

# Step 4: Build lightweight Docker image
echo "🏗️  Step 4: Building lightweight Docker image (no ML deps)..."
docker build --build-arg INCLUDE_ML_DEPS=false -t somaagent01-dev:latest .

# Step 5: Start core infrastructure
echo "⚙️  Step 5: Starting core infrastructure (Kafka, Redis, PostgreSQL, OPA)..."
make deps-up

# Step 6: Wait for infrastructure to be healthy
echo "⏳ Step 6: Waiting for infrastructure to be healthy..."
echo "Waiting for PostgreSQL..."
timeout 60 bash -c "until docker exec somaAgent01_postgres pg_isready -U soma -d somaagent01; do sleep 2; done"
echo "Waiting for Redis..."
timeout 30 bash -c "until docker exec somaAgent01_redis redis-cli ping; do sleep 1; done"
echo "Waiting for Kafka..."
timeout 60 bash -c "until docker exec somaAgent01_kafka bash -c '</dev/tcp/localhost/9092'; do sleep 2; done"
echo "Waiting for OPA..."
timeout 30 bash -c "until curl -f http://localhost:20009/health; do sleep 1; done"

# Step 7: Start application services
echo "🎯 Step 7: Starting application services with FastA2A..."
make dev-up

# Step 8: Wait for gateway to be healthy
echo "🏥 Step 8: Waiting for Gateway to be healthy..."
timeout 120 bash -c "until curl -f http://localhost:21016/v1/health; do sleep 3; done"

# Step 9: Verify FastA2A services
echo "🔗 Step 9: Verifying FastA2A services..."
echo "Checking FastA2A Gateway..."
timeout 60 bash -c "until curl -f http://localhost:21017/health; do sleep 3; done"
echo "Checking FastA2A Worker..."
timeout 30 bash -c "until docker logs somaAgent01_fasta2a-worker | grep -q 'ready'; do sleep 2; done"

# Step 10: Display deployment status
echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo "========================"
echo "🌐 Gateway & UI:     http://localhost:21016/ui"
echo "🔗 FastA2A API:     http://localhost:21017"
echo "📊 Flower Monitor:  http://localhost:21018"
echo "📈 Prometheus:      http://localhost:21016/metrics"
echo ""
echo "🔍 Service Health Checks:"
echo "  Gateway:         curl http://localhost:21016/v1/health"
echo "  FastA2A Gateway: curl http://localhost:21017/health"
echo "  Dependencies:    make deps-logs"
echo ""
echo "📋 Service Logs:"
echo "  All services:    make dev-logs"
echo "  FastA2A only:    make dev-logs-svc SERVICES=fasta2a-gateway fasta2a-worker"
echo ""
echo "🛑 To stop:        make dev-down"
echo "🔄 To restart:     make dev-rebuild"
echo ""
echo "🎯 VIBE CODING RULES COMPLIANT: Real implementations, no placeholders, zero legacy patterns"