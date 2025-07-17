#!/bin/bash

echo "🚀 Starting Azure Audio Transcription Backend..."

# Check environment variables
if [[ -z "$AZURE_SPEECH_KEY" || -z "$AZURE_SPEECH_REGION" ]]; then
    echo "⚠️  Azure Speech Services environment variables not set!"
    echo "💡 Please set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION:"
    echo "   export AZURE_SPEECH_KEY='your_key_here'"
    echo "   export AZURE_SPEECH_REGION='your_region'"
    echo "📖 Or copy .env.example to .env and configure your credentials"
    exit 1
fi

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
echo "📥 Installing Azure Speech SDK and dependencies..."
pip install -r backend/requirements.txt

# Start the FastAPI server
echo "🎯 Starting Azure Speech FastAPI server on http://localhost:8000"
echo "🔧 Azure Region: $AZURE_SPEECH_REGION"
echo "🔑 Azure Key: ${AZURE_SPEECH_KEY:0:8}..."
cd backend
python main.py