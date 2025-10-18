#!/bin/bash

# ARCHITECTURE CLEANUP SCRIPT
# Removes unused files and dependencies to create a minimal working system

echo "🧹 Cleaning up architecture..."

# Remove unused requirement files (keep only minimal)
echo "Removing unused requirement files..."
rm -f requirements-ai-*.txt
rm -f requirements-audio-*.txt
rm -f requirements-browser.txt
rm -f requirements-documents.txt
rm -f requirements-grpc.txt
rm -f requirements-integrations.txt
rm -f requirements-monitoring.txt
rm -f requirements-dev.txt

# Remove unused Docker files
echo "Removing unused Docker files..."
rm -f docker-compose.canonical.yaml
rm -f docker-compose.essential.yaml
rm -f docker-compose.optimized.yaml
rm -f Dockerfile.canonical

# Remove unused services (keep only essential ones)
echo "Removing unused service directories..."
rm -rf services/delegation_gateway/
rm -rf services/delegation_worker/
rm -rf services/voice/

# Remove unused documentation (keep only essential)
echo "Cleaning up documentation..."
rm -rf site/
rm -f docs.zip

# Remove unused scripts
echo "Removing unused scripts..."
rm -f scripts/capsule_smoke.py
rm -f scripts/loadtest_k6.js
rm -f scripts/persona_training.py
rm -f scripts/run_load_test.js

# Remove legacy files
echo "Removing legacy files..."
rm -f CONTAINER_ANALYSIS.md
rm -f OPTIMIZED_ARCHITECTURE.md
rm -f ROADMAP_*.md
rm -f SPRINT_PLAN.md
rm -f SOMAGENT_TOOL_SERVICE_DESIGN.md
rm -f TOOL_EXECUTOR_DESIGN.md

# Clean up Python cache
echo "Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Remove unused directories
echo "Removing unused directories..."
rm -rf a0_data/
rm -rf infra/

echo "✅ Architecture cleanup complete!"
echo ""
echo "🚀 To start the minimal system:"
echo "   make minimal-up"
echo ""
echo "📊 To check status:"
echo "   make minimal-ps"
echo ""
echo "📝 To view logs:"
echo "   make minimal-logs"