# 🎤 Azure Speech Audio Transcription - Testing Guide

## Overview
Your Azure-powered audio transcription application is now ready for testing! The system includes:
- **Azure Speech Services**: Professional-grade transcription engine
- **FastAPI Backend**: Handles audio processing and Azure integration
- **Gradio Frontend**: User-friendly web interface with real-time updates
- **Two Transcription Modes**: 
  - Fast (Azure Real-time API)
  - Batch (Azure Batch API)
- **Conversation Export**: Complete transcriptions saved to text files

## 🚀 Quick Test Setup

### Prerequisites
1. **Azure Speech Service configured** (see `AZURE_SETUP.md`)
2. **Environment variables set**:
   ```bash
   export AZURE_SPEECH_KEY="your_azure_key"
   export AZURE_SPEECH_REGION="your_azure_region"
   ```

### Option 1: Use Startup Scripts (Recommended)

1. **Terminal 1 - Start Azure Backend**:
   ```bash
   ./start_backend.sh
   ```
   
2. **Terminal 2 - Start Frontend**:
   ```bash
   ./start_frontend.sh
   ```

### Option 2: Manual Start

1. **Terminal 1 - Start Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   export AZURE_SPEECH_KEY="your_key"
   export AZURE_SPEECH_REGION="your_region"
   python main.py
   ```
   
2. **Terminal 2 - Start Frontend**:
   ```bash
   cd frontend
   source venv/bin/activate
   python app.py
   ```

## 🌐 Access Points

- **Frontend (Gradio UI)**: http://localhost:7860
- **Backend API Docs**: http://localhost:8000/docs
- **Backend Health Check**: http://localhost:8000

## 🎯 Testing Features

### 1. Test Fast Transcription Mode
1. Open http://localhost:7860
2. Select "Fast Transcription" from dropdown
3. Enable "Use Microphone" checkbox
4. Click "🎙️ Start Recording"
5. Watch real-time transcriptions appear in the "Real-time Transcription" box
6. Click "⏹️ Stop Recording" to see final results

### 2. Test Batch Transcription Mode
1. Select "Batch Transcription" from dropdown
2. Enable "Use Microphone" checkbox  
3. Click "🎙️ Start Recording"
4. Notice no real-time transcriptions (they're queued)
5. Click "⏹️ Stop Recording" to process all chunks together
6. View complete transcription in "Final Transcription" box

### 3. Test API Directly
Use the interactive API docs at http://localhost:8000/docs to test:
- `POST /create_session` - Create new session
- `POST /upload_audio` - Upload audio chunks
- `POST /batch_transcribe` - Process batch transcription
- `GET /session/{session_id}/transcriptions` - Get results

## 🔧 Current Configuration

### Demo Mode Settings
- **Audio Duration**: 10 seconds per chunk (for quick testing)
- **Audio Source**: Simulated sine wave (440Hz tone)
- **Transcription**: Uses Google Speech Recognition API (free tier)

### Production Changes Needed
To use with real microphone input:
1. Replace simulated audio generation in `frontend/app.py`
2. Add real microphone capture using `pyaudio` or `sounddevice`
3. Change chunk duration from 10s to 120s (2 minutes)

## 📊 Expected Behavior

### Fast Mode
- ✅ Audio chunks processed immediately
- ✅ Real-time transcription updates every 10 seconds
- ✅ Status updates show processing progress
- ✅ Final transcription combines all chunks

### Batch Mode  
- ✅ Audio chunks stored but not processed
- ✅ "Stored for batch processing" messages
- ✅ All processing happens when "Stop" is clicked
- ✅ Single comprehensive transcription result

## 🐛 Troubleshooting

### Backend Issues
```bash
# Check if backend is running
curl http://localhost:8000

# View backend logs in terminal
# Look for FastAPI startup messages
```

### Frontend Issues
```bash
# Check if frontend can reach backend
# Look for connection errors in browser console
# Verify backend URL in frontend/app.py (line 16)
```

### Audio/Transcription Issues
- **Internet required**: Google Speech Recognition needs internet connection
- **Audio format**: Currently uses simulated audio (440Hz sine wave)
- **Transcription accuracy**: Free tier has limitations

## 🔄 Session Flow

1. **Start Recording** → Creates new session in backend
2. **Audio Chunks** → Every 10 seconds, audio sent to backend  
3. **Processing** → Fast mode: immediate transcription, Batch mode: queued
4. **Stop Recording** → Batch mode triggers processing, results displayed
5. **Cleanup** → Session ends, temporary files removed

## 📁 File Storage

Audio files are temporarily stored in:
```
backend/audio_files/{session_id}/
├── chunk_1.wav
├── chunk_2.wav
└── chunk_N.wav
```

## 🎯 Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:7860
- [ ] Can create sessions via API
- [ ] Fast mode shows real-time updates
- [ ] Batch mode processes all at once
- [ ] Audio files are stored correctly
- [ ] Sessions cleanup properly
- [ ] Error handling works (try invalid sessions)

## 🔧 Customization Options

### Change Audio Duration
Edit `frontend/app.py` line ~167:
```python
chunk_duration = 120  # Change from 10 to 120 for 2-minute chunks
```

### Change Transcription Service
Edit `backend/main.py` function `transcribe_audio()` to use different APIs:
- OpenAI Whisper
- Azure Speech Services  
- Amazon Transcribe
- Local speech recognition models

### Modify UI
Edit `frontend/app.py` to customize:
- Interface layout
- Button styles
- Status messages
- Real-time update frequency

## 🎉 Success Indicators

You'll know it's working when you see:
- ✅ Backend: "Audio Transcription API is running!" 
- ✅ Frontend: Clean interface with all controls
- ✅ Fast mode: Text appearing in real-time box
- ✅ Batch mode: Final transcription after stopping
- ✅ API docs: Interactive documentation loads

The app is now ready for testing and can be extended with real microphone input for production use!