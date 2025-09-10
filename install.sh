#!/bin/bash
set -e

echo "[Humanizer] Checking Python & pip..."
if ! command -v python3 &>/dev/null; then
    echo "Python3 not found. Installing..."
    sudo apt update && sudo apt install -y python3 python3-venv python3-pip
fi

if ! command -v pip3 &>/dev/null; then
    echo "pip not found. Installing..."
    sudo apt install -y python3-pip
fi

echo "[Humanizer] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[Humanizer] Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[Humanizer] Installed successfully. Run with: ./run.sh"
