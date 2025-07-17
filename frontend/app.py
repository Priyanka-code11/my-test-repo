import gradio as gr
import requests
import time
import json
import threading
import queue
import numpy as np
from datetime import datetime
import io
import wave
import tempfile
import os

# Backend URL
BACKEND_URL = "http://localhost:8000"

# Global variables
current_session_id = None
is_recording = False
chunk_counter = 0
recording_thread = None
transcriptions = []

def create_session():
    """Create a new session with the backend"""
    try:
        response = requests.post(f"{BACKEND_URL}/create_session")
        if response.status_code == 200:
            return response.json()["session_id"]
        else:
            return None
    except Exception as e:
        print(f"Error creating session: {e}")
        return None

def upload_audio_chunk(session_id, approach, chunk_id, audio_data):
    """Upload audio chunk to backend"""
    try:
        # Convert audio data to WAV format
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            # Write WAV header and data
            with wave.open(tmp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(audio_data.tobytes())
            
            # Upload to backend
            with open(tmp_file.name, 'rb') as audio_file:
                files = {'audio_file': audio_file}
                data = {
                    'session_id': session_id,
                    'approach': approach,
                    'chunk_id': chunk_id
                }
                response = requests.post(f"{BACKEND_URL}/upload_audio", files=files, data=data)
                
            # Cleanup temp file
            os.unlink(tmp_file.name)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Upload failed: {response.text}"}
                
    except Exception as e:
        return {"error": f"Error uploading audio: {str(e)}"}

def batch_transcribe(session_id):
    """Request batch transcription for all chunks"""
    try:
        data = {'session_id': session_id}
        response = requests.post(f"{BACKEND_URL}/batch_transcribe", data=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Batch transcription failed: {response.text}"}
    except Exception as e:
        return {"error": f"Error in batch transcription: {str(e)}"}

def start_recording(approach, microphone_input):
    """Start recording audio"""
    global current_session_id, is_recording, chunk_counter, recording_thread, transcriptions
    
    if is_recording:
        return "Already recording!", gr.update(), gr.update()
    
    # Create new session
    current_session_id = create_session()
    if not current_session_id:
        return "Failed to create session!", gr.update(), gr.update()
    
    is_recording = True
    chunk_counter = 0
    transcriptions = []
    
    # Start recording in a separate thread
    recording_thread = threading.Thread(
        target=record_audio_chunks, 
        args=(approach, microphone_input)
    )
    recording_thread.start()
    
    return (
        f"Recording started! Session: {current_session_id[:8]}...\nApproach: {approach}",
        gr.update(interactive=False),  # Disable start button
        gr.update(interactive=True)    # Enable stop button
    )

def stop_recording():
    """Stop recording audio"""
    global is_recording, current_session_id, transcriptions
    
    if not is_recording:
        return "Not currently recording!", gr.update(), gr.update(), ""
    
    is_recording = False
    
    # Wait for recording thread to finish
    if recording_thread:
        recording_thread.join(timeout=5)
    
    final_transcription = ""
    
    # If batch mode, request batch transcription
    if transcriptions and len(transcriptions) > 0:
        # Check if we need to do batch processing
        if any("Stored for batch processing" in t.get("transcription", "") for t in transcriptions):
            batch_result = batch_transcribe(current_session_id)
            if "error" not in batch_result:
                final_transcription = batch_result.get("full_transcription", "")
            else:
                final_transcription = f"Error: {batch_result['error']}"
        else:
            # Combine fast transcriptions
            final_transcription = "\n".join([
                f"[Chunk {t.get('chunk_id', 'N/A')}]: {t.get('transcription', 'No transcription')}"
                for t in transcriptions
            ])
    
    status_msg = f"Recording stopped! Processed {len(transcriptions)} chunks."
    
    return (
        status_msg,
        gr.update(interactive=True),   # Enable start button
        gr.update(interactive=False),  # Disable stop button
        final_transcription
    )

def record_audio_chunks(approach, microphone_input):
    """Record audio in 2-minute chunks"""
    global is_recording, chunk_counter, current_session_id, transcriptions
    
    while is_recording:
        try:
            # Simulate 2-minute recording (shortened for demo - 10 seconds)
            chunk_duration = 10  # seconds (change to 120 for actual 2 minutes)
            
            # Simulate audio recording (in real implementation, this would capture from microphone)
            # For demo purposes, we'll create a simple sine wave
            sample_rate = 16000
            duration = chunk_duration
            samples = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))
            audio_data = (samples * 32767).astype(np.int16)
            
            chunk_counter += 1
            
            # Upload chunk to backend
            result = upload_audio_chunk(current_session_id, approach.lower(), chunk_counter, audio_data)
            
            if "error" not in result:
                transcriptions.append(result)
                print(f"Chunk {chunk_counter} processed: {result.get('transcription', 'No transcription')}")
            else:
                print(f"Error processing chunk {chunk_counter}: {result['error']}")
            
            # Wait before next chunk (or until stopped)
            for _ in range(chunk_duration):
                if not is_recording:
                    break
                time.sleep(1)
                
        except Exception as e:
            print(f"Error in recording loop: {e}")
            break

def get_real_time_transcription():
    """Get real-time transcription updates for fast mode"""
    global transcriptions
    
    if not transcriptions:
        return "No transcriptions yet..."
    
    # Return the latest transcriptions
    recent_transcriptions = []
    for t in transcriptions[-5:]:  # Show last 5 chunks
        if t.get("status") == "processed":
            recent_transcriptions.append(
                f"[Chunk {t.get('chunk_id')}] {t.get('timestamp', '')[:19]}: {t.get('transcription', '')}"
            )
    
    return "\n".join(recent_transcriptions) if recent_transcriptions else "Processing..."

# Create Gradio interface
with gr.Blocks(title="Audio Transcription App", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎤 Audio Transcription Application")
    gr.Markdown("Record audio and get transcriptions using Fast or Batch processing modes.")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Settings")
            
            approach_dropdown = gr.Dropdown(
                choices=["Fast Transcription", "Batch Transcription"],
                value="Fast Transcription",
                label="Select AI Approach",
                info="Fast: Real-time processing, Batch: Process all at once"
            )
            
            microphone_checkbox = gr.Checkbox(
                label="Use Microphone",
                value=True,
                info="Enable microphone input"
            )
            
            with gr.Row():
                start_btn = gr.Button("🎙️ Start Recording", variant="primary")
                stop_btn = gr.Button("⏹️ Stop Recording", variant="stop", interactive=False)
        
        with gr.Column(scale=2):
            gr.Markdown("### Status & Results")
            
            status_display = gr.Textbox(
                label="Status",
                value="Ready to start recording...",
                interactive=False,
                lines=3
            )
            
            real_time_transcription = gr.Textbox(
                label="Real-time Transcription (Fast Mode)",
                value="",
                interactive=False,
                lines=5
            )
            
            final_transcription = gr.Textbox(
                label="Final Transcription",
                value="",
                interactive=False,
                lines=10
            )
    
    # Event handlers
    start_btn.click(
        fn=start_recording,
        inputs=[approach_dropdown, microphone_checkbox],
        outputs=[status_display, start_btn, stop_btn]
    )
    
    stop_btn.click(
        fn=stop_recording,
        outputs=[status_display, start_btn, stop_btn, final_transcription]
    )
    
    # Auto-update real-time transcription every 3 seconds
    def update_realtime():
        return get_real_time_transcription()
    
    # Set up periodic update for real-time transcription
    app.load(lambda: gr.update(), every=3).then(
        fn=update_realtime,
        outputs=[real_time_transcription]
    )
    
    with gr.Row():
        gr.Markdown("""
        ### Instructions:
        1. **Select Approach**: Choose between Fast (real-time) or Batch (process all at once) transcription
        2. **Enable Microphone**: Make sure microphone access is enabled
        3. **Start Recording**: Click to begin audio capture in 2-minute chunks
        4. **Monitor Progress**: Watch real-time transcriptions (Fast mode) or wait for final results (Batch mode)
        5. **Stop Recording**: Click to end session and get final transcription
        
        **Note**: This demo uses simulated audio. In production, replace with actual microphone input.
        """)

if __name__ == "__main__":
    # Check if backend is running
    try:
        response = requests.get(f"{BACKEND_URL}/")
        if response.status_code == 200:
            print("✅ Backend is running!")
        else:
            print("❌ Backend is not responding properly")
    except:
        print("❌ Backend is not running! Please start the FastAPI server first.")
        print("Run: cd backend && python main.py")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True
    )