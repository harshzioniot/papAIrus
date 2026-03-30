import asyncio
import os
import torch
from services.stt_service import STTService


async def test_transcription():
    """
    Test script for STT service (supports both API and local backends).
    Place a test audio file in the uploads directory and update the filename below.
    """
    
    print("🎤 Testing STT Service\n")
    
    backend = os.getenv("WHISPER_BACKEND", "").lower()
    if not backend:
        backend = "api" if os.getenv("OPENAI_API_KEY") else "local"
    
    print(f"Backend: {backend.upper()}")
    
    if backend == "local":
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"🖥️  Device: {device.upper()}")
            if device == "cuda":
                print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
        except ImportError:
            print("⚠️  PyTorch not available")
    else:
        print("☁️  Using OpenAI Whisper API")
    
    print()
    
    test_audio_file = "uploads/test_audio.mp3"
    
    if not os.path.exists(test_audio_file):
        print(f"❌ Test audio file not found: {test_audio_file}")
        print("Please place a test audio file in the uploads directory")
        print("Supported formats: mp3, mp4, wav, webm, m4a, flac")
        return
    
    try:
        print(f"📁 Transcribing: {test_audio_file}")
        print("⏳ Processing...\n")
        
        stt = STTService()
        
        transcript = await stt.transcribe_audio(test_audio_file)
        
        print("✅ Transcription successful!")
        print(f"\n📝 Transcript:\n{transcript}\n")
        
        print("\n🔍 Testing with timestamps...")
        result = await stt.transcribe_with_timestamps(test_audio_file)
        
        print(f"✅ Language detected: {result['language']}")
        print(f"⏱️  Duration: {result['duration']:.2f} seconds")
        print(f"📊 Segments: {len(result.get('segments', []))}")
        print(f"📊 Words: {len(result.get('words', []))}")
        
    except Exception as e:
        print(f"❌ Transcription Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_transcription())
