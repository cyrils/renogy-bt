#!/bin/bash
# Setup script for renogy-bt with uv

set -e

echo "========================================"
echo "Renogy BT Setup Script"
echo "========================================"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Warning: This project is designed for Linux systems (Raspberry Pi OS, Debian, Ubuntu)"
    echo "You may encounter compatibility issues on other platforms."
    echo ""
fi

# Install system dependencies
echo "Step 1: Installing system dependencies..."
echo "This requires sudo access to install system packages."
echo ""

if command -v apt-get &> /dev/null; then
    echo "Detected apt package manager (Debian/Ubuntu/Raspberry Pi OS)"
    sudo apt-get update
    sudo apt-get install -y \
        python3-dev \
        python3-dbus \
        python3-gi \
        python3-cairo \
        libdbus-1-dev \
        libglib2.0-dev \
        libcairo2-dev \
        pkg-config \
        gir1.2-gtk-3.0
    echo "✓ System dependencies installed"
else
    echo "Error: apt-get not found. Please manually install the following packages:"
    echo "  - python3-dev"
    echo "  - python3-dbus"
    echo "  - python3-gi (PyGObject)"
    echo "  - python3-cairo"
    echo "  - libdbus-1-dev"
    echo "  - libglib2.0-dev"
    echo "  - libcairo2-dev"
    echo "  - pkg-config"
    exit 1
fi

echo ""
echo "Step 2: Installing uv (if not already installed)..."
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "✓ uv installed"
else
    echo "✓ uv is already installed"
fi

echo ""
echo "Step 3: Detecting system Python version..."
# Get the system's default python3 version
SYSTEM_PYTHON=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
SYSTEM_PYTHON_FULL=$(python3 --version 2>&1 | awk '{print $2}')
echo "Detected system Python: $SYSTEM_PYTHON_FULL"
echo "System packages (python3-dbus, python3-gi, python3-cairo) are built for Python $SYSTEM_PYTHON"
echo "Using Python $SYSTEM_PYTHON for virtual environment to ensure compatibility"
echo "✓ Python version detected"

echo ""
echo "Step 4: Creating virtual environment and installing Python dependencies..."
# Create venv with system Python version and system site packages access
echo "Creating virtual environment with Python $SYSTEM_PYTHON and --system-site-packages..."
uv venv --python $SYSTEM_PYTHON --system-site-packages
uv sync
echo "✓ Virtual environment created and dependencies installed"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Update config.ini with your device MAC addresses"
echo "2. Run: uv run python example.py config.ini"
echo ""
echo "To activate the virtual environment manually:"
echo "  source .venv/bin/activate"
echo ""
