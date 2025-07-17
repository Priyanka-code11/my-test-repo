#!/bin/bash

echo "🚀 Starting Audio Transcription Backend..."

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment
source backend/venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r backend/requirements.txt

# Start the FastAPI server
echo "🎯 Starting FastAPI server on http://localhost:8000"
cd backend
python main.py