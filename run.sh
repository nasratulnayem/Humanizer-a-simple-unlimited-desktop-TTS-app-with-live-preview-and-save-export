#!/bin/bash
# ====================================
# Humanizer Runner (Linux / WSL)
# ====================================

set -e  # stop on error

echo "🚀 Starting Humanizer setup..."

# Step 1: Ensure Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[+] Python3 not found. Installing..."
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip
fi

# Step 2: Ensure pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "[+] pip not found. Installing..."
    sudo apt install -y python3-pip
fi

# Step 3: Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "[+] Creating virtual environment..."
    python3 -m venv .venv
fi

# Step 4: Activate venv
source .venv/bin/activate

# Step 5: Upgrade pip
echo "[+] Upgrading pip..."
pip install --upgrade pip

# Step 6: Install requirements
if [ -f "requirements.txt" ]; then
    echo "[+] Installing dependencies..."
    pip install -r requirements.txt
else
    echo "[!] requirements.txt not found!"
fi

# Step 7: Run the app
echo "[+] Starting Humanizer..."
python main.py
