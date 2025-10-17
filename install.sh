#!/bin/bash
# Installation script for StratMancer (Linux/Mac)

echo "=========================================="
echo "StratMancer Installation"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Setup .env
if [ ! -f .env ]; then
    echo ""
    echo "Setting up .env file..."
    cp .env.example .env
    echo "✅ .env created"
    echo "⚠️  Please edit .env and add your Riot API key"
else
    echo ""
    echo "✅ .env already exists"
fi

# Create directories
echo ""
echo "Creating directories..."
mkdir -p data/raw
mkdir -p data/processed
mkdir -p logs
echo "✅ Directories created"

# Run status check
echo ""
echo "Running status check..."
python3 check_status.py

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Riot API key"
echo "2. Run: python3 quickstart.py"
echo "3. Read: GET_STARTED.md"
echo ""

