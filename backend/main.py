from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
import json
import asyncio
from datetime import datetime
import speech_recognition as sr
import tempfile
from typing import List, Optional
import shutil

app = FastAPI(title="Audio Transcription API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class SessionResponse(BaseModel):
    session_id: str
    status: str

class TranscriptionResponse(BaseModel):
    session_id: str
    chunk_id: int
    transcription: str
    timestamp: str
    status: str

class BatchTranscriptionResponse(BaseModel):
    session_id: str
    full_transcription: str
    chunk_count: int
    status: str

# Global storage for sessions
sessions = {}
audio_storage = "audio_files"

# Ensure audio storage directory exists
os.makedirs(audio_storage, exist_ok=True)

# Initialize speech recognizer
recognizer = sr.Recognizer()

@app.get("/")
async def root():
    return {"message": "Audio Transcription API is running!"}

@app.post("/create_session", response_model=SessionResponse)
async def create_session():
    """Create a new transcription session"""
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(audio_storage, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    sessions[session_id] = {
        "created_at": datetime.now().isoformat(),
        "chunks": [],
        "transcriptions": [],
        "status": "active"
    }
    
    return SessionResponse(session_id=session_id, status="created")

@app.post("/upload_audio", response_model=TranscriptionResponse)
async def upload_audio(
    session_id: str = Form(...),
    approach: str = Form(...),  # "fast" or "batch"
    chunk_id: int = Form(...),
    audio_file: UploadFile = File(...)
):
    """Upload audio chunk and process based on approach"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if sessions[session_id]["status"] != "active":
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Save audio file
    session_dir = os.path.join(audio_storage, session_id)
    audio_filename = f"chunk_{chunk_id}.wav"
    audio_path = os.path.join(session_dir, audio_filename)
    
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
    
    # Store chunk info
    chunk_info = {
        "chunk_id": chunk_id,
        "filename": audio_filename,
        "path": audio_path,
        "timestamp": datetime.now().isoformat()
    }
    sessions[session_id]["chunks"].append(chunk_info)
    
    transcription = ""
    
    if approach.lower() == "fast":
        # Process immediately for fast transcription
        try:
            transcription = await transcribe_audio(audio_path)
            sessions[session_id]["transcriptions"].append({
                "chunk_id": chunk_id,
                "transcription": transcription,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            transcription = f"Error transcribing audio: {str(e)}"
    
    elif approach.lower() == "batch":
        # Store for batch processing later
        transcription = "Stored for batch processing"
    
    return TranscriptionResponse(
        session_id=session_id,
        chunk_id=chunk_id,
        transcription=transcription,
        timestamp=datetime.now().isoformat(),
        status="processed" if approach.lower() == "fast" else "queued"
    )

@app.post("/batch_transcribe", response_model=BatchTranscriptionResponse)
async def batch_transcribe(session_id: str = Form(...)):
    """Process all audio chunks in batch for a session"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    if not session["chunks"]:
        raise HTTPException(status_code=400, detail="No audio chunks found for this session")
    
    # Process all chunks
    full_transcription = []
    
    for chunk in session["chunks"]:
        try:
            transcription = await transcribe_audio(chunk["path"])
            full_transcription.append(f"[Chunk {chunk['chunk_id']}]: {transcription}")
            
            # Store individual transcription
            session["transcriptions"].append({
                "chunk_id": chunk["chunk_id"],
                "transcription": transcription,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            full_transcription.append(f"[Chunk {chunk['chunk_id']}]: Error - {str(e)}")
    
    # Mark session as completed
    session["status"] = "completed"
    
    combined_transcription = "\n".join(full_transcription)
    
    return BatchTranscriptionResponse(
        session_id=session_id,
        full_transcription=combined_transcription,
        chunk_count=len(session["chunks"]),
        status="completed"
    )

@app.get("/session/{session_id}/transcriptions")
async def get_session_transcriptions(session_id: str):
    """Get all transcriptions for a session"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "transcriptions": sessions[session_id]["transcriptions"],
        "status": sessions[session_id]["status"]
    }

@app.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a session and cleanup"""
    
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Mark session as ended
    sessions[session_id]["status"] = "ended"
    
    # Optional: cleanup audio files
    session_dir = os.path.join(audio_storage, session_id)
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
    
    return {"message": f"Session {session_id} ended and cleaned up"}

async def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file using speech_recognition library"""
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            # Using Google Speech Recognition (free tier)
            transcription = recognizer.recognize_google(audio)
            return transcription
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError as e:
        return f"Could not request results; {e}"
    except Exception as e:
        return f"Error processing audio: {str(e)}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)