#!/bin/bash

# MVC Test Orchestrator Installation Script (Linux/Mac)

set -e

echo "🎯 MVC Test Orchestrator v1.2 - Installation Script"
echo "=================================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION found"

# Check if Python version is 3.9 or higher
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "❌ Python 3.9 or higher is required. You have Python $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment (optional but recommended)
read -p "Do you want to create a virtual environment? (recommended) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv .venv
    
    echo "✅ Virtual environment created at .venv"
    echo "📝 To activate it, run: source .venv/bin/activate"
    echo ""
    
    # Activate virtual environment
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Dependencies installed successfully"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "🔑 Creating .env file..."
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ .env file created from env.example"
    else
        echo "GOOGLE_API_KEY=your_api_key_here" > .env
        echo "✅ .env file created"
    fi
    echo "⚠️  Please edit .env and add your Google Gemini API key!"
    echo "   Get your API key from: https://makersuite.google.com/app/apikey"
else
    echo ""
    echo "✅ .env file already exists"
fi

# Create data directory
echo ""
echo "📁 Creating data directory..."
mkdir -p data
echo "✅ Data directory created"

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env file and add your GOOGLE_API_KEY"
echo "   2. Run: python -m src.cli.mvc_arch_cli --help"
echo ""
echo "💡 Example usage:"
echo "   python -m src.cli.mvc_arch_cli create-srs --user-idea \"Your project idea\" --output data/srs_document.txt"
echo ""

