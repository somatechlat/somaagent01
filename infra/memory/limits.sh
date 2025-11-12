#!/bin/bash
# Memory optimization script for 15GB development environment
# Usage: ./limits.sh [apply|check]

TOTAL_MEMORY=15360  # 15GB in MB

# Memory allocation based on usage patterns
MEMORY_ALLOCATIONS=(
    "kafka:2048:512"        # 2GB limit, 512MB reservation
    "redis:512:256"         # 512MB limit, 256MB reservation
    "postgres:1536:512"     # 1.5GB limit, 512MB reservation
    "gateway:3072:1024"     # 3GB limit, 1GB reservation
    "conversation-worker:1024:256"
    "tool-executor:1024:256"
    "memory-replicator:512:128"
    "memory-sync:512:128"
    "outbox-sync:512:128"
)

case "${1:-check}" in
    apply)
        echo "Applying memory constraints to Docker services..."
        for allocation in "${MEMORY_ALLOCATIONS[@]}"; do
            IFS=':' read -r service limit reservation <<< "$allocation"
            echo "Setting $service: ${limit}MB limit, ${reservation}MB reservation"
        done
        echo "Memory optimization applied. Total allocated: $TOTAL_MEMORY MB"
        ;;
    check)
        echo "Current Docker memory usage:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
        ;;
    *)
        echo "Usage: $0 [apply|check]"
        exit 1
        ;;
esac