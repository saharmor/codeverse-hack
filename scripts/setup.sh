#!/bin/bash

echo "🚀 Setting up Tauri + Next.js + FastAPI Boilerplate"
echo "=================================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js v18 or later."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8 or later."
    exit 1
fi

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
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

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