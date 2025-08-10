#!/bin/bash

echo "🏗️  Building Tauri + Next.js + FastAPI Application"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Please run this script from the project root directory."
    exit 1
fi

# Build frontend
echo "⚛️  Building Next.js frontend..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi

echo "✅ Frontend built successfully!"

# Build Tauri desktop app
echo "🖥️  Building Tauri desktop application..."
npm run tauri:build

if [ $? -ne 0 ]; then
    echo "❌ Tauri build failed!"
    exit 1
fi

echo ""
echo "🎉 Build complete!"
echo ""
echo "📁 Build outputs:"
echo "   Frontend: ./out/"
echo "   Desktop:  ./src-tauri/target/release/"
echo ""
echo "🚀 Your application is ready for distribution!" 