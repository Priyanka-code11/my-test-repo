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
current_approach = "fast"

def check_backend_status():
    """Check if Azure backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            data = response.json()
            azure_configured = data.get("azure_speech_configured", False)
            region = data.get("azure_speech_region", "unknown")
            return f"✅ Azure Speech Backend Online | Region: {region} | Configured: {'✅' if azure_configured else '❌'}"
        else:
            return "❌ Backend responding but unhealthy"
    except Exception as e:
        return "❌ Backend not running - Please start the FastAPI server"

def create_session():
    """Create a new session with the Azure backend"""
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
    """Upload audio chunk to Azure backend"""
    temp_file_path = None
    try:
        # Create temporary file with manual cleanup for Windows compatibility
        temp_file_path = tempfile.mktemp(suffix=".wav")
        
        # Write WAV header and data
        with wave.open(temp_file_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # 16kHz
            wav_file.writeframes(audio_data.tobytes())
        
        # Ensure the wave file is fully closed before reading
        time.sleep(0.1)  # Small delay to ensure file is released
        
        # Upload to Azure backend
        with open(temp_file_path, 'rb') as audio_file:
            files = {'audio_file': ('audio.wav', audio_file, 'audio/wav')}
            data = {
                'session_id': session_id,
                'approach': approach,
                'chunk_id': chunk_id
            }
            response = requests.post(f"{BACKEND_URL}/upload_audio", files=files, data=data)
        
        # Cleanup temp file with retry for Windows
        try:
            os.unlink(temp_file_path)
        except (PermissionError, FileNotFoundError):
            # Try again after a short delay
            time.sleep(0.2)
            try:
                os.unlink(temp_file_path)
            except (PermissionError, FileNotFoundError):
                print(f"Warning: Could not delete temporary file {temp_file_path}")
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Upload failed: {response.text}"}
            
    except Exception as e:
        # Ensure cleanup even on error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass
        return {"error": f"Error uploading audio: {str(e)}"}

def process_batch_transcription(session_id):
    """Request batch transcription for all chunks using Azure Batch API"""
    try:
        data = {'session_id': session_id}
        response = requests.post(f"{BACKEND_URL}/process_batch", data=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Batch transcription failed: {response.text}"}
    except Exception as e:
        return {"error": f"Error in batch transcription: {str(e)}"}

def get_conversation_transcription(session_id):
    """Get the complete conversation transcription and save to file"""
    try:
        data = {'session_id': session_id}
        response = requests.post(f"{BACKEND_URL}/get_conversation_transcription", data=data)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to get conversation transcription: {response.text}"}
    except Exception as e:
        return {"error": f"Error getting conversation transcription: {str(e)}"}

def start_recording(approach, microphone_input):
    """Start recording audio"""
    global current_session_id, is_recording, chunk_counter, recording_thread, transcriptions, current_approach
    
    if is_recording:
        return "Already recording!", gr.update(), gr.update(), gr.update()
    
    # Create new session
    current_session_id = create_session()
    if not current_session_id:
        return "Failed to create session with Azure backend!", gr.update(), gr.update(), gr.update()
    
    # Map approach names
    approach_map = {
        "Fast Transcription": "fast",
        "Batch Transcription": "batch"
    }
    current_approach = approach_map.get(approach, "fast")
    
    is_recording = True
    chunk_counter = 0
    transcriptions = []
    
    # Start recording in a separate thread
    recording_thread = threading.Thread(
        target=record_audio_chunks, 
        args=(current_approach, microphone_input)
    )
    recording_thread.start()
    
    return (
        f"🎤 Recording started!\n📋 Session: {current_session_id[:8]}...\n🔧 Approach: {approach}\n⏱️ Recording 2-min chunks...",
        gr.update(interactive=False),  # Disable start button
        gr.update(interactive=True),   # Enable stop button
        ""  # Clear conversation display
    )

def stop_recording():
    """Stop recording audio and get complete conversation transcription"""
    global is_recording, current_session_id, transcriptions, current_approach
    
    if not is_recording:
        return "Not currently recording!", gr.update(), gr.update(), "", ""
    
    is_recording = False
    
    # Wait for recording thread to finish
    if recording_thread:
        recording_thread.join(timeout=5)
    
    status_msg = f"⏹️ Recording stopped!\n📊 Processed {len(transcriptions)} chunks\n🔄 Generating final transcription..."
    
    conversation_text = ""
    
    try:
        if current_approach == "batch":
            # For batch mode, process all chunks together
            batch_result = process_batch_transcription(current_session_id)
            if "error" not in batch_result:
                conversation_text = batch_result.get("full_transcription", "No transcription available")
            else:
                conversation_text = f"❌ Error: {batch_result['error']}"
        
        # Get the complete conversation transcription (works for both approaches)
        conversation_result = get_conversation_transcription(current_session_id)
        if "error" not in conversation_result:
            conversation_text = conversation_result.get("conversation_transcription", "No transcription available")
            file_path = conversation_result.get("file_path", "Not saved")
            status_msg += f"\n💾 Saved to: {file_path}"
        else:
            conversation_text = f"❌ Error getting conversation: {conversation_result['error']}"
            
    except Exception as e:
        conversation_text = f"❌ Error processing transcription: {str(e)}"
    
    final_status = f"✅ Recording completed!\n📈 Total chunks: {len(transcriptions)}\n📝 Transcription ready!\n🎯 Approach used: {current_approach.upper()}"
    
    return (
        final_status,
        gr.update(interactive=True),   # Enable start button
        gr.update(interactive=False),  # Disable stop button
        conversation_text,  # Display conversation transcription
        get_real_time_transcription()  # Update real-time display
    )

def record_audio_chunks(approach, microphone_input):
    """Record audio in 2-minute chunks"""
    global is_recording, chunk_counter, current_session_id, transcriptions
    
    while is_recording:
        try:
            # 2-minute chunks (shortened to 15 seconds for demo)
            chunk_duration = 15  # seconds (change to 120 for actual 2 minutes)
            
            # Simulate audio recording (in real implementation, capture from microphone)
            # Creating a more realistic audio pattern for demo
            sample_rate = 16000
            duration = chunk_duration
            
            # Generate different tones for each chunk to simulate different speech
            base_freq = 300 + (chunk_counter * 50)  # Varying frequency
            samples = np.sin(2 * np.pi * base_freq * np.linspace(0, duration, int(sample_rate * duration)))
            # Add some noise to make it more realistic
            noise = np.random.normal(0, 0.1, samples.shape)
            samples = samples + noise
            audio_data = (samples * 32767 * 0.5).astype(np.int16)
            
            chunk_counter += 1
            
            # Upload chunk to Azure backend
            result = upload_audio_chunk(current_session_id, approach, chunk_counter, audio_data)
            
            if "error" not in result:
                transcriptions.append(result)
                print(f"Chunk {chunk_counter} processed: {result.get('transcription', 'No transcription')}")
            else:
                print(f"Error processing chunk {chunk_counter}: {result['error']}")
                transcriptions.append({"error": result["error"], "chunk_id": chunk_counter})
            
            # Wait before next chunk (or until stopped)
            for _ in range(chunk_duration):
                if not is_recording:
                    break
                time.sleep(1)
                
        except Exception as e:
            print(f"Error in recording loop: {e}")
            break

def get_real_time_transcription():
    """Get real-time transcription updates"""
    global transcriptions, current_approach
    
    if not transcriptions:
        return "📭 No transcriptions yet...\n🎤 Start recording to see real-time results!"
    
    if current_approach == "batch":
        return f"📦 Batch Mode Active\n🔄 Collected {len(transcriptions)} chunks\n⏳ Transcription will be processed when you stop recording"
    
    # For fast mode, show recent transcriptions
    recent_transcriptions = []
    for t in transcriptions[-5:]:  # Show last 5 chunks
        if "error" not in t:
            transcription_preview = t.get('transcription', 'Processing...')
            if transcription_preview and not transcription_preview.startswith('['):
                recent_transcriptions.append(
                    f"🎵 Chunk {t.get('chunk_id', 'N/A')}: {transcription_preview[:100]}{'...' if len(transcription_preview) > 100 else ''}"
                )
            else:
                recent_transcriptions.append(f"🔄 Chunk {t.get('chunk_id', 'N/A')}: {transcription_preview}")
        else:
            recent_transcriptions.append(f"❌ Chunk {t.get('chunk_id', 'N/A')}: {t.get('error', 'Unknown error')}")
    
    if recent_transcriptions:
        return "🔴 LIVE TRANSCRIPTION (Fast Mode):\n" + "\n".join(recent_transcriptions)
    else:
        return "🔄 Processing audio chunks..."

# Create Gradio interface with Azure Speech Services theme
with gr.Blocks(
    title="Azure Speech Audio Transcription", 
    theme=gr.themes.Soft(),
    css=".gradio-container {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);}"
) as app:
    
    gr.Markdown("""
    # 🎤 Azure Speech Services Audio Transcription
    ### Real-time and Batch Audio Processing with Conversation Export
    """)
    
    # Backend status check
    backend_status = gr.Textbox(
        label="🔧 Backend Status",
        value=check_backend_status(),
        interactive=False,
        lines=1
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Configuration")
            
            approach_dropdown = gr.Dropdown(
                choices=["Fast Transcription", "Batch Transcription"],
                value="Fast Transcription",
                label="🤖 Select Transcription Approach",
                info="Fast: Azure Real-time API | Batch: Azure Batch API"
            )
            
            microphone_checkbox = gr.Checkbox(
                label="🎙️ Use Microphone",
                value=True,
                info="Enable microphone input (simulated in demo)"
            )
            
            gr.Markdown("### 🎛️ Controls")
            
            with gr.Row():
                start_btn = gr.Button("🎙️ Start Recording", variant="primary", size="lg")
                stop_btn = gr.Button("⏹️ Stop Recording", variant="stop", interactive=False, size="lg")
        
        with gr.Column(scale=2):
            gr.Markdown("### 📊 Live Status & Results")
            
            status_display = gr.Textbox(
                label="📋 Recording Status",
                value="Ready to start recording with Azure Speech Services...",
                interactive=False,
                lines=4
            )
            
            real_time_transcription = gr.Textbox(
                label="⚡ Real-time Transcription",
                value="",
                interactive=False,
                lines=6,
                placeholder="Real-time results will appear here during Fast Transcription mode..."
            )
    
    # Conversation transcription display (shown after stopping)
    conversation_display = gr.Textbox(
        label="💬 Complete Conversation Transcription",
        value="",
        interactive=False,
        lines=12,
        placeholder="Complete conversation transcription will appear here when you stop recording..."
    )
    
    # Event handlers
    start_btn.click(
        fn=start_recording,
        inputs=[approach_dropdown, microphone_checkbox],
        outputs=[status_display, start_btn, stop_btn, conversation_display]
    )
    
    stop_btn.click(
        fn=stop_recording,
        outputs=[status_display, start_btn, stop_btn, conversation_display, real_time_transcription]
    )
    
    # Auto-update real-time transcription every 2 seconds
    def update_components():
        return get_real_time_transcription(), check_backend_status()
    
    # Set up periodic updates (compatible with different Gradio versions)
    try:
        # For newer Gradio versions (4.0+)
        app.load(lambda: None, every=2).then(
            fn=update_components,
            outputs=[real_time_transcription, backend_status]
        )
    except TypeError:
        # For older Gradio versions, use a different approach
        print("📝 Note: Using compatibility mode for older Gradio version")
        print("💡 For auto-updates, please upgrade Gradio: pip install --upgrade gradio")
        
        # Fallback: Manual refresh button for older versions
        refresh_btn = gr.Button("🔄 Refresh Status", size="sm")
        refresh_btn.click(
            fn=update_components,
            outputs=[real_time_transcription, backend_status]
        )
    
    with gr.Accordion("📖 Instructions", open=False):
        gr.Markdown("""
        ### How to Use:
        
        1. **🔧 Check Backend**: Ensure Azure Speech Services backend is running and configured
        2. **🤖 Select Approach**: 
           - **Fast Transcription**: Uses Azure Real-time Speech API for immediate results
           - **Batch Transcription**: Uses Azure Batch API for processing all audio at once
        3. **🎙️ Enable Microphone**: Make sure microphone access is enabled (simulated in demo)
        4. **▶️ Start Recording**: Begin audio capture in 2-minute chunks
        5. **👀 Monitor Progress**: 
           - **Fast Mode**: Watch real-time transcriptions appear
           - **Batch Mode**: See chunk collection progress
        6. **⏹️ Stop Recording**: End session and get complete conversation transcription
        7. **💾 File Export**: Conversation is automatically saved to text file for later processing
        
        ### Features:
        - ✅ Azure Speech Services integration
        - ✅ Real-time transcription (Fast mode)
        - ✅ Batch processing (Batch mode)
        - ✅ Conversation export to text file
        - ✅ Session management
        - ✅ Error handling
        
        **Note**: This demo uses simulated audio. In production, replace with actual microphone input.
        """)
    
    gr.Markdown("""
    ---
    **Powered by Azure Speech Services** | **FastAPI Backend** | **Gradio Frontend**
    """)

if __name__ == "__main__":
    print("🚀 Starting Azure Speech Audio Transcription Frontend...")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True,
        show_api=False
    )