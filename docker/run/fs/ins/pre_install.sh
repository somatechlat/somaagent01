#!/bin/bash
set -e

# update apt and install essential system packages for heavy Python libs
apt-get update

# Core build tools for compiling wheels
apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    wget \
    git \
    curl \
    pkg-config \
    unzip \
    zip \
    sudo

# Audio & multimedia libs (python-soundfile, ffmpeg backends)
apt-get install -y --no-install-recommends \
    libsndfile1 \
    libsndfile1-dev \
    ffmpeg \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev

# Support for faiss (OpenMP runtime) and other native libs
apt-get install -y --no-install-recommends \
    libgomp1 \
    libopenblas-dev

# Playwright dependencies (minimal set for Chromium) - may be extended
apt-get install -y --no-install-recommends \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    fonts-liberation \
    libpangocairo-1.0-0

# Clean up apt caches to keep the image small
apt-get clean && rm -rf /var/lib/apt/lists/*

# fix permissions for cron files if any
if [ -f /etc/cron.d/* ]; then
    chmod 0644 /etc/cron.d/*
fi

# Prepare SSH daemon
bash /ins/setup_ssh.sh "$@"
