#!/bin/bash

# Inner Joy Studio Automation - Setup Script
# This script automates the initial setup process

echo "====================================="
echo "Inner Joy Studio Automation Setup"
echo "====================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.10 or higher required. Found Python $python_version"
    exit 1
fi
echo "✓ Python $python_version found"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your actual credentials!"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Create directories if they don't exist
echo "Checking directories..."
mkdir -p templates
mkdir -p static
mkdir -p services
echo "✓ Directory structure verified"
echo ""

# Check for Google credentials
if [ ! -f "credentials.json" ]; then
    echo "⚠️  WARNING: Google credentials file not found!"
    echo "Please download credentials.json from Google Cloud Console"
    echo "and place it in the project root directory."
    echo ""
else
    echo "✓ Google credentials found"
    echo ""
fi

echo "====================================="
echo "Setup Complete!"
echo "====================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Download credentials.json from Google Cloud Console (if not done)"
echo "3. Create custom fields in Respond.io (see QUICKSTART.md)"
echo "4. Run: python app.py"
echo "5. Initialize sheets: curl -X POST http://localhost:5000/api/initialize-sheets"
echo ""
echo "For detailed instructions, see README.md or QUICKSTART.md"
echo ""
