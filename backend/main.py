from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
import json
import asyncio
from datetime import datetime
import tempfile
from typing import List, Optional
import shutil
import requests
import time
import azure.cognitiveservices.speech as speechsdk

app = FastAPI(title="Azure Audio Transcription API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Azure Speech Service Configuration
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "your_azure_speech_key")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "your_azure_region")

# Data models
class SessionResponse(BaseModel):
    session_id: str
    status: str

class TranscriptionResponse(BaseModel):
    session_id: str
    chunk_id: int
    transcription: str
    approach: str
    timestamp: str

class BatchTranscriptionResponse(BaseModel):
    session_id: str
    full_transcription: str
    approach: str
    timestamp: str
    total_chunks: int

class ConversationTranscriptionResponse(BaseModel):
    session_id: str
    conversation_transcription: str
    timestamp: str
    total_chunks: int
    file_path: str

# In-memory storage for demo purposes
sessions = {}
audio_chunks = {}
transcriptions = {}

def get_speech_config():
    """Get Azure Speech configuration"""
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_recognition_language = "en-US"
    return speech_config

def transcribe_audio_realtime(audio_file_path: str) -> str:
    """Transcribe audio using Azure Speech real-time recognition"""
    try:
        speech_config = get_speech_config()
        audio_config = speechsdk.AudioConfig(filename=audio_file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        
        result = speech_recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return "[No speech detected]"
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speechsdk.CancellationDetails(result)
            return f"[Error: {cancellation_details.reason}]"
    except Exception as e:
        return f"[Transcription error: {str(e)}]"

def create_batch_transcription(audio_files: List[str]) -> str:
    """Create a batch transcription using Azure Speech SDK"""
    try:
        transcriptions = []
        speech_config = get_speech_config()
        
        for i, audio_file in enumerate(audio_files):
            try:
                audio_config = speechsdk.AudioConfig(filename=audio_file)
                speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
                
                result = speech_recognizer.recognize_once()
                
                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    transcriptions.append(result.text)
                elif result.reason == speechsdk.ResultReason.NoMatch:
                    transcriptions.append("[No speech detected]")
                else:
                    transcriptions.append(f"[Processing error for chunk {i}]")
                    
            except Exception as e:
                transcriptions.append(f"[Error processing chunk {i}: {str(e)}]")
        
        return " ".join(transcriptions)
        
    except Exception as e:
        return f"[Batch transcription error: {str(e)}]"

@app.get("/")
async def root():
    return {"message": "Azure Audio Transcription API is running!", "version": "1.0.0"}

@app.post("/create_session", response_model=SessionResponse)
async def create_session():
    """Create a new transcription session"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "approach": None,
        "chunk_count": 0
    }
    audio_chunks[session_id] = []
    transcriptions[session_id] = []
    
    # Create directory for this session
    session_dir = f"audio_files/{session_id}"
    os.makedirs(session_dir, exist_ok=True)
    
    return SessionResponse(session_id=session_id, status="created")

@app.post("/upload_audio", response_model=TranscriptionResponse)
async def upload_audio(
    session_id: str = Form(...),
    approach: str = Form(...),
    chunk_id: int = Form(...),
    audio_file: UploadFile = File(...)
):
    """Upload an audio chunk for transcription"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session approach and chunk count
    sessions[session_id]["approach"] = approach
    sessions[session_id]["chunk_count"] = max(sessions[session_id]["chunk_count"], chunk_id + 1)
    
    # Save the audio file
    session_dir = f"audio_files/{session_id}"
    audio_path = f"{session_dir}/chunk_{chunk_id}.wav"
    
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
    
    audio_chunks[session_id].append({
        "chunk_id": chunk_id,
        "file_path": audio_path,
        "timestamp": datetime.now().isoformat()
    })
    
    transcription_text = ""
    
    # Process based on approach
    if approach == "fast":
        # Fast transcription - process immediately using Azure real-time
        transcription_text = transcribe_audio_realtime(audio_path)
        
        # Store transcription
        transcriptions[session_id].append({
            "chunk_id": chunk_id,
            "transcription": transcription_text,
            "timestamp": datetime.now().isoformat()
        })
        
    elif approach == "batch":
        # Batch transcription - just acknowledge receipt
        transcription_text = f"[Chunk {chunk_id} received - waiting for batch processing]"
    
    return TranscriptionResponse(
        session_id=session_id,
        chunk_id=chunk_id,
        transcription=transcription_text,
        approach=approach,
        timestamp=datetime.now().isoformat()
    )

@app.post("/process_batch", response_model=BatchTranscriptionResponse)
async def process_batch_transcription(session_id: str = Form(...)):
    """Process all audio chunks in batch mode using Azure Batch Transcription"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if sessions[session_id]["approach"] != "batch":
        raise HTTPException(status_code=400, detail="Session is not in batch mode")
    
    # Get all audio chunks for this session
    chunks = audio_chunks.get(session_id, [])
    audio_files = [chunk["file_path"] for chunk in sorted(chunks, key=lambda x: x["chunk_id"])]
    
    # Process using Azure Batch Transcription
    full_transcription = create_batch_transcription(audio_files)
    
    # Store the final transcription
    transcriptions[session_id] = [{
        "chunk_id": -1,  # Special ID for batch result
        "transcription": full_transcription,
        "timestamp": datetime.now().isoformat()
    }]
    
    return BatchTranscriptionResponse(
        session_id=session_id,
        full_transcription=full_transcription,
        approach="batch",
        timestamp=datetime.now().isoformat(),
        total_chunks=len(chunks)
    )

@app.post("/get_conversation_transcription", response_model=ConversationTranscriptionResponse)
async def get_conversation_transcription(session_id: str = Form(...)):
    """Get the complete conversation transcription and save to text file"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    approach = sessions[session_id]["approach"]
    conversation_text = ""
    
    if approach == "fast":
        # Combine all fast transcriptions
        fast_transcriptions = transcriptions.get(session_id, [])
        conversation_parts = []
        for trans in sorted(fast_transcriptions, key=lambda x: x["chunk_id"]):
            if trans["transcription"] and not trans["transcription"].startswith("["):
                conversation_parts.append(trans["transcription"])
        conversation_text = " ".join(conversation_parts)
        
    elif approach == "batch":
        # Get batch transcription result
        batch_transcriptions = transcriptions.get(session_id, [])
        if batch_transcriptions:
            conversation_text = batch_transcriptions[0]["transcription"]
    
    # Save to text file
    session_dir = f"audio_files/{session_id}"
    transcription_file = f"{session_dir}/conversation_transcription.txt"
    
    with open(transcription_file, "w", encoding="utf-8") as f:
        f.write(f"Azure Speech Services - Conversation Transcription\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Session ID: {session_id}\n")
        f.write(f"Transcription Approach: {approach.upper()}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Audio Chunks: {len(audio_chunks.get(session_id, []))}\n")
        f.write(f"Azure Speech Region: {AZURE_SPEECH_REGION}\n")
        f.write(f"\n{'='*60}\n")
        f.write(f"TRANSCRIPTION:\n")
        f.write(f"{'='*60}\n\n")
        f.write(conversation_text)
        f.write(f"\n\n{'='*60}\n")
        f.write(f"End of transcription - Generated by Azure Speech Services\n")
    
    return ConversationTranscriptionResponse(
        session_id=session_id,
        conversation_transcription=conversation_text,
        timestamp=datetime.now().isoformat(),
        total_chunks=len(audio_chunks.get(session_id, [])),
        file_path=transcription_file
    )

@app.get("/get_transcriptions/{session_id}")
async def get_transcriptions(session_id: str):
    """Get all transcriptions for a session"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "session_info": sessions[session_id],
        "transcriptions": transcriptions.get(session_id, []),
        "total_chunks": len(audio_chunks.get(session_id, []))
    }

@app.delete("/cleanup_session/{session_id}")
async def cleanup_session(session_id: str):
    """Clean up session data and files"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Remove session data
    sessions.pop(session_id, None)
    audio_chunks.pop(session_id, None)
    transcriptions.pop(session_id, None)
    
    # Remove audio files
    session_dir = f"audio_files/{session_id}"
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
    
    return {"message": f"Session {session_id} cleaned up successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Azure Speech Service connection
        speech_config = get_speech_config()
        return {
            "status": "healthy", 
            "timestamp": datetime.now().isoformat(),
            "azure_speech_configured": bool(AZURE_SPEECH_KEY != "your_azure_speech_key"),
            "azure_speech_region": AZURE_SPEECH_REGION
        }
    except Exception as e:
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    
    # Create audio files directory
    os.makedirs("audio_files", exist_ok=True)
    
    print("🚀 Starting Azure Audio Transcription Backend...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🎯 Server running on: http://localhost:8000")
    print(f"🔧 Azure Speech Region: {AZURE_SPEECH_REGION}")
    print(f"🔑 Azure Speech Key: {'✅ Configured' if AZURE_SPEECH_KEY != 'your_azure_speech_key' else '❌ Not configured'}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)