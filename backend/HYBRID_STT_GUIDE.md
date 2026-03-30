# Hybrid Whisper STT - Complete Guide

## ✅ Module 1: Speech-to-Text (STT) - HYBRID MODE

Your STT module now supports **BOTH** OpenAI API and Local Whisper! Switch between them with a simple environment variable.

---

## 🎯 Quick Comparison

| Feature | OpenAI API | Local Whisper |
|---------|-----------|---------------|
| **Cost** | $0.006/min | FREE |
| **Speed** | Fast | 10-20x faster with GPU |
| **Setup** | API key only | Model download (~1-10GB) |
| **Internet** | Required | Offline |
| **Accuracy** | High | High (model dependent) |
| **Best For** | Quick start, no GPU | Production, GPU server |

---

## 🚀 Setup Instructions

### Option 1: OpenAI API (Cloud)

**1. Get API Key**
- Visit: https://platform.openai.com/api-keys
- Create new key

**2. Configure**
```bash
# Windows CMD
set WHISPER_BACKEND=api
set OPENAI_API_KEY=sk-your-key-here

# PowerShell
$env:WHISPER_BACKEND="api"
$env:OPENAI_API_KEY="sk-your-key-here"

# Linux/Mac
export WHISPER_BACKEND=api
export OPENAI_API_KEY=sk-your-key-here
```

**3. Install & Run**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---

### Option 2: Local Whisper (GPU/CPU)

**1. Configure**
```bash
# Windows CMD
set WHISPER_BACKEND=local
set WHISPER_MODEL_SIZE=base

# PowerShell
$env:WHISPER_BACKEND="local"
$env:WHISPER_MODEL_SIZE="base"

# Linux/Mac
export WHISPER_BACKEND=local
export WHISPER_MODEL_SIZE=base
```

**Model Sizes:**
- `tiny` - ~1GB, fastest
- `base` - ~1GB, balanced (default)
- `small` - ~2GB, better accuracy
- `medium` - ~5GB, high accuracy (GPU recommended)
- `large` - ~10GB, best accuracy (GPU required)

**2. Install & Run**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

First run will download the model (~1-10GB depending on size).

---

## 🔄 Switching Backends

The service automatically detects which backend to use:

1. **If `WHISPER_BACKEND` is set**: Uses that backend
2. **If `OPENAI_API_KEY` is set**: Defaults to API
3. **Otherwise**: Defaults to local

**Example: Start with API, switch to local later**
```bash
# Start with API
set WHISPER_BACKEND=api
set OPENAI_API_KEY=sk-xxx
uvicorn main:app --reload

# Later, switch to local (restart server)
set WHISPER_BACKEND=local
uvicorn main:app --reload
```

---

## 🧪 Testing

### Test Script
```bash
# Place test audio in backend/uploads/test_audio.mp3
python test_stt.py
```

**Expected Output (API):**
```
🎤 Testing STT Service

Backend: API
☁️  Using OpenAI Whisper API

📁 Transcribing: uploads/test_audio.mp3
⏳ Processing...

✅ Transcription successful!
```

**Expected Output (Local):**
```
🎤 Testing STT Service

Backend: LOCAL
🖥️  Device: CUDA
🎮 GPU: NVIDIA GeForce RTX 3080

📁 Transcribing: uploads/test_audio.mp3
⏳ Processing...

✅ Transcription successful!
```

### API Endpoints
Both backends use the same endpoints:

**1. Transcribe existing entry**
```bash
POST /entries/{entry_id}/transcribe
```

**2. Quick transcription**
```bash
curl -X POST "http://localhost:8000/entries/transcribe-upload" \
  -F "audio=@recording.mp3"
```

---

## 📊 Performance Comparison

### OpenAI API
- **Speed**: ~2-5 seconds per minute of audio
- **Consistency**: Always fast, cloud-powered
- **Cost**: $0.006/min ($0.36/hour of audio)

### Local Whisper (GPU)
- **Speed**: ~3-6 seconds per minute (base model)
- **Speed**: ~10-20 seconds per minute (large model)
- **Cost**: FREE (one-time model download)

### Local Whisper (CPU)
- **Speed**: ~30-60 seconds per minute (base model)
- **Cost**: FREE
- **Note**: Use smaller models (tiny/base) for better speed

---

## 💡 Recommendations

### For Development
- **Use API**: Quick setup, no model downloads
- Set `WHISPER_BACKEND=api`

### For Production (with GPU)
- **Use Local**: Free, fast with GPU, offline
- Set `WHISPER_BACKEND=local`
- Use `medium` or `large` model for best accuracy

### For Production (CPU only)
- **Use API**: More reliable than slow CPU inference
- Or use local with `tiny`/`base` model

### For Testing/Prototyping
- **Use API**: Fastest to get started
- Switch to local once you're ready to deploy

---

## 🔧 Environment Variables Summary

```bash
# Backend selection
WHISPER_BACKEND=api          # or "local"

# API backend (required if WHISPER_BACKEND=api)
OPENAI_API_KEY=sk-xxx

# Local backend (optional, used if WHISPER_BACKEND=local)
WHISPER_MODEL_SIZE=base      # tiny|base|small|medium|large

# MongoDB (always required)
MONGO_URI=mongodb://localhost:27017
DB_NAME=papairus
```

---

## 🐛 Troubleshooting

### "OPENAI_API_KEY environment variable required"
- You set `WHISPER_BACKEND=api` but didn't provide API key
- **Fix**: Set `OPENAI_API_KEY` or switch to `WHISPER_BACKEND=local`

### "Model download is slow"
- First run downloads model from Hugging Face
- **Fix**: Be patient, it only happens once. Models are cached at `~/.cache/whisper/`

### "CUDA out of memory"
- Model too large for your GPU
- **Fix**: Use smaller model (`base` or `small` instead of `large`)

### "Transcription is slow on CPU"
- CPU inference is naturally slower
- **Fix**: Use smaller model (`tiny` or `base`) or switch to API

---

## ✨ Features Implemented

- ✅ **Dual backend support** (API + Local)
- ✅ **Automatic backend detection**
- ✅ **Configurable model sizes** (local)
- ✅ **GPU acceleration** (local)
- ✅ **Word-level timestamps** (both)
- ✅ **Multi-language support** (both)
- ✅ **Async processing** (both)
- ✅ **Same API interface** (seamless switching)

---

## 📝 Next Steps

Now that STT is working with both backends, you can:

1. **Test both backends** to see which works best for you
2. **Commit your changes** with hybrid support
3. **Move to Module 2**: Emotion/Theme extraction from transcripts
4. **Deploy**: Choose backend based on your infrastructure

**Status: Module 1 (STT) - HYBRID MODE READY** 🎉
