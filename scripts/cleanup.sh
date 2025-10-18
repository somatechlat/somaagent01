#!/bin/bash

echo "Cleaning up unnecessary files before Docker build..."

# Remove caches and temporary files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type d -name ".ruff_cache" -exec rm -rf {} +
find . -type d -name ".mypy_cache" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type f -name "*.pyd" -delete
find . -type f -name ".DS_Store" -delete
find . -type f -name "*.log" -delete

# Remove large directories that aren't needed
rm -rf tmp/*
rm -rf logs/*
rm -rf .venv
rm -rf docs/res
rm -rf webui/vendor
rm -rf archived
rm -rf a0_data
rm -rf tmp/playwright

echo "Cleanup complete! You can now build the Docker image."