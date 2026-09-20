#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 English 7 Grounded Learning Platform contributors
# SPDX-License-Identifier: Apache-2.0

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$PATH:/home/nguyenphuong/.local/opt/flutter/bin"

echo "=================================================="
echo " 🚀 English 7 Grounded Learning Platform"
echo "=================================================="

# 1. Start backend services if not already running
echo "[1/2] Checking Backend containers (Docker)..."
if ! docker compose ps | grep -q "english7-api.*Up"; then
    echo "Starting Docker containers..."
    docker compose up -d
else
    echo "Backend containers are already running."
fi

# 2. Launch Flutter App
echo "[2/2] Launching Flutter Mobile App..."
cd "$DIR/mobile"

# Prefer connected Android emulator, Chrome, or specified device
if [ "$1" = "android" ]; then
    flutter run -d emulator-5554
elif [ "$1" = "linux" ]; then
    flutter run -d linux
elif [ "$1" = "chrome" ]; then
    flutter run -d chrome
else
    if flutter devices | grep -q "emulator-"; then
        flutter run -d emulator-5554
    else
        flutter run -d chrome
    fi
fi
