# Speech-to-Text (STT) Service

## Overview
This module provides Speech-to-Text functionality using **local OpenAI Whisper models** for the papAIrus voice companion project.

## Features
- **Local Audio Transcription**: Convert audio files to text using Whisper models running on your hardware
- **GPU Acceleration**: Automatic CUDA support for faster processing
- **Timestamp Support**: Get word-level timestamps for detailed analysis
- **Multi-language Support**: Transcribe audio in 99+ languages
- **Async Operations**: Non-blocking audio processing
- **Model Caching**: Models are loaded once and cached for performance
- **FREE**: No API costs, runs completely offline

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note:** First run will download the Whisper model (~1-10GB depending on size)

### 2. Configure Model Size (Optional)

**Windows (Command Prompt):**
```cmd
set WHISPER_MODEL_SIZE=base
```

**Windows (PowerShell):**
```powershell
$env:WHISPER_MODEL_SIZE="base"
```

**Linux/Mac:**
```bash
export WHISPER_MODEL_SIZE=base
```

**Model Options:**
- `tiny` - Fastest, ~1GB (good for testing)
- `base` - Default, ~1GB (good balance)
- `small` - Better accuracy, ~2GB
- `medium` - High accuracy, ~5GB
- `large` - Best accuracy, ~10GB

## API Endpoints

### 1. Transcribe Existing Entry
**POST** `/entries/{entry_id}/transcribe`

Transcribes the audio file associated with an existing entry and updates its transcript field.

**Query Parameters:**
- `language` (optional): ISO-639-1 language code (e.g., 'en', 'es', 'fr')

**Response:** Returns the updated `EntryOut` object with the transcript

**Example:**
```bash
curl -X POST "http://localhost:8000/entries/123/transcribe?language=en"
```

### 2. Transcribe Upload (Quick Test)
**POST** `/entries/transcribe-upload`

Transcribes an uploaded audio file without creating an entry. Useful for testing.

**Form Data:**
- `audio`: Audio file (required)
- `language`: ISO-639-1 language code (optional)
- `with_timestamps`: Boolean, get word-level timestamps (optional)

**Response:** 
```json
{
  "text": "transcribed text here"
}
```

Or with timestamps:
```json
{
  "text": "transcribed text here",
  "language": "en",
  "duration": 12.5,
  "words": [...]
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/entries/transcribe-upload" \
  -F "audio=@recording.mp3" \
  -F "language=en" \
  -F "with_timestamps=true"
```

## Supported Audio Formats
- MP3
- MP4
- MPEG
- MPGA
- M4A
- WAV
- WEBM

## Usage in Code

```python
from services import stt_service

# Simple transcription
transcript = await stt_service.transcribe_audio(
    audio_file_path="/path/to/audio.mp3",
    language="en"  # optional, auto-detects if not specified
)
print(transcript)

# With timestamps and segments
result = await stt_service.transcribe_with_timestamps(
    audio_file_path="/path/to/audio.mp3",
    language="en"
)
print(result["text"])
print(f"Language: {result['language']}")
print(f"Duration: {result['duration']}s")
print(f"Segments: {len(result['segments'])}")
print(f"Words: {len(result['words'])}")

# Access word-level timestamps
for word_info in result["words"]:
    print(f"{word_info['word']}: {word_info['start']:.2f}s - {word_info['end']:.2f}s")
```

## Performance Tips

1. **Model stays loaded**: First transcription loads model, subsequent calls reuse it
2. **Use GPU**: Automatic CUDA detection for 10-20x speedup
3. **Choose right model**: `base` for speed, `medium`/`large` for accuracy
4. **Batch processing**: Process multiple files without restarting server

## Error Handling
The service raises exceptions with descriptive messages:
- Model loading failures: `Exception` with details
- Transcription failures: `Exception` with details
- File not found: Standard Python exceptions

## Next Steps
- [ ] Add audio preprocessing (noise reduction, normalization)
- [ ] Implement speaker diarization
- [ ] Add support for streaming audio
- [ ] Cache transcriptions to avoid re-processing
- [ ] Add custom vocabulary/prompts for better accuracy
- [ ] Implement batch processing endpoint
