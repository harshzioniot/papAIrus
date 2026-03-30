# papAIrus - Quick Start Guide

## ✅ What's Ready

**Module 1: Speech-to-Text (STT)** - COMPLETE
- ✅ Hybrid backend (OpenAI API + Local Whisper)
- ✅ Voice recording in frontend
- ✅ Audio transcription
- ✅ Text-only, Audio-only, or Both modes
- ✅ Auto-tagging (stub)

---

## 🚀 Quick Start (Cloud API Version)

### Backend Setup

1. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Set environment variables**
```bash
# Windows CMD
set WHISPER_BACKEND=api
set OPENAI_API_KEY=sk-your-key-here
set MONGO_URI=mongodb://localhost:27017

# PowerShell
$env:WHISPER_BACKEND="api"
$env:OPENAI_API_KEY="sk-your-key-here"
$env:MONGO_URI="mongodb://localhost:27017"
```

3. **Start MongoDB** (if not running)
```bash
# Windows - if you have MongoDB installed
mongod

# Or use Docker
docker run -d -p 27017:27017 mongo
```

4. **Start backend**
```bash
uvicorn main:app --reload
```

Backend will be at: `http://localhost:8000`

---

### Frontend Setup

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Start frontend**
```bash
npm run dev
```

Frontend will be at: `http://localhost:3000`

---

## 🎤 Using the Voice Companion

### 1. Navigate to Record Page
Open `http://localhost:3000/record`

### 2. Choose Input Mode
- **📝 Text** - Type only (no audio)
- **🎤 Audio** - Record only (with transcription)
- **📝+🎤 Both** - Record + type (default)

### 3. Create an Entry

**Text Mode:**
1. Type your thoughts in the textarea
2. Add tags (optional)
3. Click "Save entry"

**Audio Mode:**
1. Hold the orb to record
2. Release to stop
3. Click "✨ Transcribe" to convert to text
4. Add tags (optional)
5. Click "Save entry"

**Both Mode:**
1. Record audio OR type text (or both!)
2. Transcribe if needed
3. Add tags
4. Save

---

## 🧪 Testing STT

### Test 1: Quick Transcription (No Entry)
```bash
cd backend
python test_stt.py
```

Place a test audio file at `backend/uploads/test_audio.mp3` first.

### Test 2: Via API
```bash
curl -X POST "http://localhost:8000/entries/transcribe-upload" \
  -F "audio=@your_audio.mp3"
```

### Test 3: Via Frontend
1. Go to `/record`
2. Select "🎤 Audio" mode
3. Hold orb to record
4. Click "✨ Transcribe"
5. See text appear!

---

## 📊 API Endpoints

### Entries
- `POST /entries` - Create entry (with optional audio)
- `GET /entries` - List all entries
- `GET /entries/{id}` - Get specific entry
- `DELETE /entries/{id}` - Delete entry
- `POST /entries/{id}/transcribe` - Transcribe entry's audio
- `POST /entries/transcribe-upload` - Quick transcribe (no entry)
- `POST /entries/{id}/auto-tag` - Auto-tag entry (stub)
- `POST /entries/{id}/tags` - Set entry tags

### Nodes
- `GET /nodes` - List all nodes
- `POST /nodes` - Create node

### Graph & Digest
- `GET /graph` - Get knowledge graph
- `GET /digest` - Get weekly digest

---

## 🔧 Configuration Options

### Backend (.env or environment variables)

```bash
# MongoDB
MONGO_URI=mongodb://localhost:27017
DB_NAME=papairus

# STT Backend
WHISPER_BACKEND=api              # or "local"

# For API backend
OPENAI_API_KEY=sk-xxx

# For local backend (no API key needed!)
WHISPER_MODEL_SIZE=base          # tiny|base|small|medium|large
```

---

## 🎯 Input Modes Explained

### Text Mode (📝)
- **Use case**: Quick journaling, no audio needed
- **Features**: Type directly, add tags, save
- **Best for**: Desktop users, quiet environments

### Audio Mode (🎤)
- **Use case**: Voice-only journaling
- **Features**: Record, transcribe, add tags, save
- **Best for**: Mobile users, hands-free, driving

### Both Mode (📝+🎤)
- **Use case**: Flexible input
- **Features**: Record AND/OR type, transcribe, edit, save
- **Best for**: Maximum flexibility, editing transcripts

---

## 💡 Tips

1. **Transcription is optional** - You can save audio without transcribing
2. **Edit transcripts** - Transcription isn't perfect, edit as needed
3. **Add tags manually** - Auto-tag is a stub, add your own tags
4. **Audio is saved** - Original audio is kept even after transcription
5. **Switch modes anytime** - Change input mode without losing data

---

## 🐛 Troubleshooting

### "Failed to fetch" / "Network error"
- Check backend is running at `http://localhost:8000`
- Check MongoDB is running
- Check CORS settings in backend

### "Transcription failed"
- **API mode**: Check `OPENAI_API_KEY` is set and valid
- **Local mode**: Check model is downloaded (first run takes time)
- Check backend logs for errors

### "Microphone access denied"
- Browser needs microphone permission
- Check browser settings
- Try HTTPS (required for some browsers)

### "No audio recorded"
- Hold the orb longer (minimum ~1 second)
- Check microphone is working
- Try a different browser

---

## 📁 Project Structure

```
papAIrus/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── models.py            # MongoDB models
│   ├── schemas.py           # Pydantic schemas
│   ├── routers/
│   │   ├── entries.py       # Entry endpoints
│   │   ├── nodes.py         # Node endpoints
│   │   ├── graph.py         # Graph endpoint
│   │   └── digest.py        # Digest endpoint
│   ├── services/
│   │   └── stt_service.py   # STT service (hybrid)
│   ├── uploads/             # Audio files
│   └── requirements.txt
│
└── frontend/
    ├── app/
    │   ├── record/          # Voice recording page
    │   ├── history/         # Entry history
    │   ├── graph/           # Knowledge graph
    │   └── digest/          # Weekly digest
    ├── components/
    │   ├── Sidebar.tsx
    │   └── NodeChip.tsx
    └── lib/
        └── api.ts           # API client

```

---

## ✨ What's Next?

**Module 2: Emotion/Theme Extraction**
- Replace auto-tag stub with real NLP
- Extract emotions, themes, people, habits from transcripts
- Auto-create and link nodes

**Module 3: Knowledge Graph**
- Build connections between entries
- Visualize relationships
- Find patterns over time

**Module 4: Weekly Digest**
- Generate insights from week's entries
- Mood trends, streaks, reflections
- AI-powered summaries

---

## 🎉 You're Ready!

Start the backend and frontend, then go to `/record` and create your first entry!

**Questions?** Check:
- `backend/STT_SETUP.md` - Detailed STT setup
- `backend/HYBRID_STT_GUIDE.md` - Hybrid backend guide
- `backend/services/README.md` - Service documentation
