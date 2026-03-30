import os
import asyncio
from typing import Optional
from functools import lru_cache
import aiofiles


class STTService:
    def __init__(self):
        """
        Initialize STT service with configurable backend.
        
        Backend is determined by WHISPER_BACKEND env var:
        - "api" or "openai": Use OpenAI Whisper API (requires OPENAI_API_KEY)
        - "local": Use local Whisper model (requires GPU/CPU, downloads model)
        
        Default: "local" if no API key, otherwise "api"
        """
        self.backend = os.getenv("WHISPER_BACKEND", "").lower()
        
        if not self.backend:
            if os.getenv("OPENAI_API_KEY"):
                self.backend = "api"
            else:
                self.backend = "local"
        
        print(f"🎤 STT Backend: {self.backend.upper()}")
        
        if self.backend in ["api", "openai"]:
            self._init_api_backend()
        else:
            self._init_local_backend()
    
    def _init_api_backend(self):
        """Initialize OpenAI API backend"""
        from openai import AsyncOpenAI
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable required for API backend. "
                "Set WHISPER_BACKEND=local to use local model instead."
            )
        self.client = AsyncOpenAI(api_key=api_key)
        print("✓ Using OpenAI Whisper API")
    
    def _init_local_backend(self):
        """Initialize local Whisper backend"""
        try:
            import whisper
            import torch
        except ImportError as e:
            raise ImportError(
                f"Local Whisper dependencies not installed: {e}\n\n"
                "To use local Whisper, install additional dependencies:\n"
                "  pip install -r requirements-local.txt\n\n"
                "Or switch to API backend:\n"
                "  set WHISPER_BACKEND=api\n"
                "  set OPENAI_API_KEY=your-key-here"
            )
        
        self.model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.whisper = whisper
        self.torch = torch
        print(f"✓ Using Local Whisper (device: {self.device}, model: {self.model_size})")
    
    def _ensure_model_loaded(self):
        """Lazy load the local model on first use"""
        if self.model is None:
            print(f"Loading Whisper {self.model_size} model on {self.device}...")
            self.model = self.whisper.load_model(self.model_size, device=self.device)
            print(f"✓ Model loaded successfully")
    
    async def transcribe_audio(
        self, 
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        Transcribe audio file using configured backend.
        
        Args:
            audio_file_path: Path to the audio file
            language: Optional ISO-639-1 language code (e.g., 'en', 'es')
            prompt: Optional text to guide the model's style
            
        Returns:
            Transcribed text
        """
        if self.backend in ["api", "openai"]:
            return await self._transcribe_api(audio_file_path, language, prompt)
        else:
            return await self._transcribe_local(audio_file_path, language, prompt)
    
    async def transcribe_with_timestamps(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio with word-level timestamps.
        
        Returns:
            Dictionary with text, language, duration, and segments/words
        """
        if self.backend in ["api", "openai"]:
            return await self._transcribe_api_timestamps(audio_file_path, language)
        else:
            return await self._transcribe_local_timestamps(audio_file_path, language)
    
    # ── OpenAI API Backend ────────────────────────────────────────────────────
    
    async def _transcribe_api(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """Transcribe using OpenAI API"""
        try:
            async with aiofiles.open(audio_file_path, 'rb') as audio_file:
                audio_data = await audio_file.read()
            
            filename = os.path.basename(audio_file_path)
            
            transcription = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=(filename, audio_data),
                language=language,
                prompt=prompt,
                response_format="text"
            )
            
            return transcription.strip()
            
        except Exception as e:
            raise Exception(f"API transcription failed: {str(e)}")
    
    async def _transcribe_api_timestamps(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> dict:
        """Transcribe with timestamps using OpenAI API"""
        try:
            async with aiofiles.open(audio_file_path, 'rb') as audio_file:
                audio_data = await audio_file.read()
            
            filename = os.path.basename(audio_file_path)
            
            transcription = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=(filename, audio_data),
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
            
            return {
                "text": transcription.text,
                "language": transcription.language,
                "duration": transcription.duration,
                "segments": getattr(transcription, 'segments', []),
                "words": getattr(transcription, 'words', [])
            }
            
        except Exception as e:
            raise Exception(f"API transcription with timestamps failed: {str(e)}")
    
    # ── Local Whisper Backend ─────────────────────────────────────────────────
    
    async def _transcribe_local(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """Transcribe using local Whisper model"""
        try:
            self._ensure_model_loaded()
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_file_path,
                    language=language,
                    initial_prompt=prompt,
                    fp16=(self.device == "cuda")
                )
            )
            
            return result["text"].strip()
            
        except Exception as e:
            raise Exception(f"Local transcription failed: {str(e)}")
    
    async def _transcribe_local_timestamps(
        self,
        audio_file_path: str,
        language: Optional[str] = None
    ) -> dict:
        """Transcribe with timestamps using local Whisper model"""
        try:
            self._ensure_model_loaded()
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_file_path,
                    language=language,
                    word_timestamps=True,
                    fp16=(self.device == "cuda")
                )
            )
            
            words = []
            for segment in result.get("segments", []):
                if "words" in segment:
                    for word in segment["words"]:
                        words.append({
                            "word": word.get("word", ""),
                            "start": word.get("start", 0),
                            "end": word.get("end", 0)
                        })
            
            return {
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "duration": result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0,
                "segments": result.get("segments", []),
                "words": words
            }
            
        except Exception as e:
            raise Exception(f"Local transcription with timestamps failed: {str(e)}")


stt_service = STTService()
