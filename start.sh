#!/bin/bash

# MyCraftCrew Startup Script

echo "🎨 Starting MyCraftCrew..."
echo "======================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found. Please run this script from the project root directory."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads processed_images collages logs temp

# Check if dependencies are installed
echo "🔍 Checking dependencies..."
python3 -c "import fastapi, uvicorn, PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Start the server
echo "🚀 Starting server..."
echo "   API will be available at: http://localhost:8000"
echo "   Documentation at: http://localhost:8000/docs"
echo "   Press Ctrl+C to stop the server"
echo ""

python3 main.py
