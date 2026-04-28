# papAIrus - Quick Start Guide

## ✅ What's Ready

**Module 1: Speech-to-Text (STT)** - COMPLETE
- ✅ Hybrid backend (OpenAI API + Local Whisper)
- ✅ Voice recording, text/audio/both modes

**Module 2: Extraction Pipeline** - COMPLETE
- ✅ Local BERT NER + DistilRoBERTa emotion (Layer 1)
- ✅ LLM tag extraction across 8 node types (Layer 2, swappable: Gemini / OpenAI / Ollama)
- ✅ Rule-based typed edge inference, persisted to MongoDB
- ✅ Auto-fires in background on entry create + transcribe

**Module 3: Knowledge Graph** - COMPLETE
- ✅ NetworkX algorithms: PageRank centrality, community detection, trends, path finding
- ✅ `/graph/insights` and `/graph/path` endpoints
- ✅ Frontend visualisation with all 8 node types

**Module 4: Conversation Layer** - COMPLETE
- ✅ `/chat` endpoint with subgraph-grounded responses
- ✅ Three personas: Stoic Listener, Socratic, Pattern Analyst
- ✅ Frontend `/chat` page with persona selector and context-node display

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
- `POST /entries` - Create entry (auto-fires NLP + LLM + edge pipeline in background)
- `GET /entries` - List all entries
- `GET /entries/{id}` - Get specific entry
- `DELETE /entries/{id}` - Delete entry
- `POST /entries/{id}/transcribe` - Transcribe entry's audio (auto-fires pipeline)
- `POST /entries/transcribe-upload` - Quick transcribe (no entry)
- `POST /entries/{id}/auto-tag` - Manual re-tag trigger
- `POST /entries/{id}/tags` - Set entry tags

### Nodes
- `GET /nodes` - List all nodes
- `POST /nodes` - Create node

### Graph & Digest
- `GET /graph` - Visualisation graph (typed edges)
- `GET /graph/insights` - PageRank centrality + community detection + trending nodes
- `GET /graph/path?from_id=&to_id=` - Shortest causal path between two nodes
- `GET /digest` - Weekly digest (graph-informed reflection)

### Chat
- `POST /chat` - Talk to a philosopher persona, grounded in your graph
  - Body: `{ "message": "...", "persona": "stoic" | "socratic" | "analyst" }`
  - `persona` is optional; falls back to `CHAT_PERSONA` env (default: `stoic`)
  - Returns: `{ "reply": "...", "context_nodes": [...], "persona": "..." }`

---

## 🔧 Configuration Options

### Backend (.env or environment variables)

```bash
# MongoDB
MONGO_URI=mongodb://localhost:27017
DB_NAME=papairus

# STT Backend
WHISPER_BACKEND=api              # or "local"
WHISPER_MODEL_SIZE=base          # tiny|base|small|medium|large (local only)

# LLM Provider — used by analysis_service AND chat_service
LLM_PROVIDER=gemini              # gemini | openai | ollama
GEMINI_API_KEY=...               # if LLM_PROVIDER=gemini
OPENAI_API_KEY=sk-...            # if LLM_PROVIDER=openai (also used by API STT)
OLLAMA_MODEL=mistral             # if LLM_PROVIDER=ollama, also `ollama pull mistral`

# Chat
CHAT_PERSONA=stoic               # stoic | socratic | analyst (default if request omits it)
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

- Persistent multi-turn chat history (currently each `/chat` request is independent)
- Voice input on the `/chat` page (reuse the record orb)
- Streaming LLM responses
- Improved subgraph retrieval (semantic match instead of substring)
- User authentication / multi-user support

---

## 🎉 You're Ready!

Start the backend and frontend, then go to `/record` and create your first entry!

**Questions?** Check:
- `backend/STT_SETUP.md` - Detailed STT setup
- `backend/HYBRID_STT_GUIDE.md` - Hybrid backend guide
- `backend/services/README.md` - Service documentation
