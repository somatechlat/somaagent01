#!/bin/bash

# SomaAgent01 Optimized Deployment Script
# Deploys the lean 7-container architecture with dependency fixes

set -e

echo "🚀 Starting SomaAgent01 Optimized Deployment..."

# Create network if it doesn't exist
if ! docker network ls | grep -q somaagent01; then
    echo "📡 Creating Docker network..."
    docker network create somaagent01
fi

# Stop any existing services
echo "🛑 Stopping existing services..."
docker compose -f docker-compose.optimized.yaml --profile core --profile dev down || true

# Start infrastructure services first
echo "🏗️ Starting infrastructure services..."
docker compose -f docker-compose.optimized.yaml --profile core up -d kafka redis postgres opa

# Wait for infrastructure to be ready
echo "⏳ Waiting for infrastructure services to be healthy..."
timeout=180
counter=0

while [ $counter -lt $timeout ]; do
    if docker compose -f docker-compose.optimized.yaml ps --format json | jq -r '.Health // "healthy"' | grep -v healthy | grep -q .; then
        echo "   Infrastructure services starting... ($counter/$timeout seconds)"
        sleep 5
        counter=$((counter + 5))
    else
        echo "✅ Infrastructure services are healthy!"
        break
    fi
done

if [ $counter -ge $timeout ]; then
    echo "❌ Timeout waiting for infrastructure services"
    docker compose -f docker-compose.optimized.yaml logs --tail=50
    exit 1
fi

# Start agent services
echo "🤖 Starting agent services..."
docker compose -f docker-compose.optimized.yaml --profile core --profile dev up -d

# Show status
echo "📊 Service Status:"
docker compose -f docker-compose.optimized.yaml ps

echo ""
echo "🎉 Deployment complete! Services available at:"
echo "   🌐 Gateway API: http://localhost:40016"
echo "   📊 Agent UI: http://localhost:40014"
echo "   🗄️ Kafka: localhost:40001"
echo "   💾 Redis: localhost:40002"
echo "   🐘 PostgreSQL: localhost:40003"
echo "   🔐 OPA: http://localhost:40011"
echo ""
echo "📝 To check logs: docker compose -f docker-compose.optimized.yaml logs -f [service]"
echo "🔍 To check health: docker compose -f docker-compose.optimized.yaml ps"