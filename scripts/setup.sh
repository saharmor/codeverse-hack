#!/bin/bash

echo "🚀 Setting up Tauri + Next.js + FastAPI Boilerplate"
echo "=================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js v18 or later."
    exit 1
fi

# Check if Python is installed and find compatible version
PYTHON_CMD=""
PYTHON_VERSION=""

# Try to find Python 3.11 first (most compatible)
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    PYTHON_VERSION="3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    PYTHON_VERSION="3.10"
elif command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
    PYTHON_VERSION="3.9"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
else
    echo "❌ Python3 is not installed. Please install Python 3.9, 3.10, or 3.11."
    exit 1
fi

echo "✅ Found Python $PYTHON_VERSION at: $(which $PYTHON_CMD)"

# Check if Rust is installed
if ! command -v rustc &> /dev/null; then
    echo "❌ Rust is not installed. Please install Rust."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Install Tauri CLI globally
echo "🔧 Installing Tauri CLI..."
npm install -g @tauri-apps/cli

# Setup Python backend
echo "🐍 Setting up Python backend..."
cd backend

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip first
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start the backend: cd backend && python run.py"
echo "2. Start the frontend: npm run dev"
echo "3. Run the desktop app: npm run tauri:dev"
echo ""
echo "Happy coding! 🚀"
