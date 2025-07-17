# 🎤 Azure Speech Services Audio Transcription Application

A professional audio transcription application powered by Azure Speech Services, featuring FastAPI backend and Gradio frontend with both real-time and batch transcription capabilities.

## 🏗️ Architecture

- **Backend**: FastAPI with Azure Speech Services integration
- **Frontend**: Gradio web interface with live audio processing
- **Speech Services**: Azure Cognitive Services Speech-to-Text
- **Transcription Modes**: 
  - **Fast Transcription**: Azure Real-time Speech Recognition API
  - **Batch Transcription**: Azure Batch Speech Recognition API

## 📋 Features

- ✅ **Azure Speech Services Integration**: Professional-grade transcription
- ✅ **Real-time Processing**: Immediate transcription with Azure Real-time API
- ✅ **Batch Processing**: Optimized bulk transcription with Azure Batch API
- ✅ **Conversation Export**: Complete transcription saved to text files
- ✅ **Session Management**: Unique session IDs with proper cleanup
- ✅ **Live Dashboard**: Real-time status updates and progress monitoring
- ✅ **Error Handling**: Comprehensive error handling and recovery
- ✅ **Audio Chunking**: 2-minute audio segments for optimal processing

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Azure Speech Services subscription
- Audio input device (microphone)

### 1. Azure Setup

1. **Create Azure Speech Service**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a new "Speech" resource
   - Note your **subscription key** and **region**

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Azure Speech credentials
   ```

### 2. Quick Start (Recommended)

1. **Start the Backend** (in terminal 1):
   ```bash
   export AZURE_SPEECH_KEY="your_key_here"
   export AZURE_SPEECH_REGION="your_region"
   ./start_backend.sh
   ```

2. **Start the Frontend** (in terminal 2):
   ```bash
   ./start_frontend.sh
   ```

### 3. Manual Setup

#### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI server:
   ```bash
   python main.py
   ```

   The backend will be available at: `http://localhost:8000`

#### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Create and activate virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the Gradio app:
   ```bash
   python app.py
   ```

   The frontend will be available at: `http://localhost:7860`

## 🎯 Usage

1. **Open the Web Interface**: Navigate to `http://localhost:7860`

2. **Select Transcription Approach**:
   - **Fast Transcription**: Get real-time transcriptions as you speak
   - **Batch Transcription**: Get all transcriptions processed together at the end

3. **Enable Microphone**: Check the microphone option (currently uses simulated audio for demo)

4. **Start Recording**: Click "🎙️ Start Recording"

5. **Monitor Progress**: 
   - Fast mode: Watch real-time transcriptions appear
   - Batch mode: Wait for final processing

6. **Stop Recording**: Click "⏹️ Stop Recording" to get final results

## 📡 API Endpoints

### Backend API (`http://localhost:8000`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/create_session` | Create new transcription session |
| POST | `/upload_audio` | Upload audio chunk for processing |
| POST | `/batch_transcribe` | Process all chunks in batch mode |
| GET | `/session/{session_id}/transcriptions` | Get session transcriptions |
| DELETE | `/session/{session_id}` | End session and cleanup |

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## 🔧 Configuration

### Audio Settings

- **Chunk Duration**: Currently set to 10 seconds for demo (change to 120s for production)
- **Sample Rate**: 16kHz
- **Format**: Mono WAV files
- **Audio Storage**: Files stored in `backend/audio_files/`

### Transcription Service

The application uses Google Speech Recognition API (free tier). For production:

1. Consider upgrading to paid services for better accuracy
2. Add API key authentication
3. Implement fallback transcription services

## 🛠️ Development

### Project Structure

```
audio-transcription-app/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Backend dependencies
│   └── audio_files/         # Audio storage (created automatically)
├── frontend/
│   ├── app.py              # Gradio application
│   └── requirements.txt    # Frontend dependencies
├── start_backend.sh        # Backend startup script
├── start_frontend.sh       # Frontend startup script
└── README.md              # This file
```

### Adding Real Microphone Support

To replace simulated audio with real microphone input:

1. Install additional dependencies:
   ```bash
   pip install pyaudio sounddevice
   ```

2. Replace the simulated audio generation in `frontend/app.py` with actual microphone capture
3. Update the audio format handling as needed

### Extending Transcription Services

To add more transcription providers:

1. Create new transcription functions in `backend/main.py`
2. Add provider selection to the API
3. Update frontend to include provider options

## 🐛 Troubleshooting

### Common Issues

1. **Backend not starting**:
   - Check if port 8000 is available
   - Ensure all dependencies are installed
   - Check Python version (3.8+ required)

2. **Frontend can't connect to backend**:
   - Verify backend is running on `http://localhost:8000`
   - Check CORS settings if accessing from different domain

3. **Audio transcription errors**:
   - Ensure internet connection for Google Speech API
   - Check audio file format and quality
   - Verify microphone permissions

4. **Permission errors**:
   - Make startup scripts executable: `chmod +x *.sh`
   - Check file system permissions for audio storage

### Logs

- Backend logs: Check terminal running the FastAPI server
- Frontend logs: Check browser console and terminal running Gradio
- Audio files: Check `backend/audio_files/` directory

## 📄 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes and test thoroughly
4. Submit pull request with detailed description

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `http://localhost:8000/docs`
3. Check application logs for error details

---

**Note**: This demo uses simulated audio for testing. For production use, implement actual microphone capture and consider using professional transcription services.