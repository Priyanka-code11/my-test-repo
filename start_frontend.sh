#!/bin/bash

echo "🎨 Starting Audio Transcription Frontend..."

# Check if virtual environment exists
if [ ! -d "frontend/venv" ]; then
    echo "📦 Creating virtual environment..."
    cd frontend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment
source frontend/venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r frontend/requirements.txt

# Start the Gradio app
echo "🎯 Starting Gradio app on http://localhost:7860"
cd frontend
python app.py