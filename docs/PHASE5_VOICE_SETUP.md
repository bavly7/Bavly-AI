# Phase 5 — Voice I/O Setup Guide

> Planning document for Speech-to-Text (STT) and Text-to-Speech (TTS) integration.
> Created: 2026-09-25

## Overview

Phase 5 adds voice input/output to the Bavly chatbot, allowing users to speak their questions and hear responses. Voice I/O is implemented as an input/output layer on top of the existing text-based RAG pipeline — the core LangGraph flow remains unchanged.

**Tech decisions (from TASKS.md):**
- **STT**: Groq Whisper-large-v3 API
- **TTS**: Edge TTS library (`en-US-GuyNeural` for English, `ar-EG-ShakirNeural` for Egyptian Arabic)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (browser)                                          │
│  - MediaRecorder API captures audio                         │
│  - POST audio to /api/stt                                   │
│  - Display transcribed text + send to existing chat flow    │
│  - Receive text response + request TTS via /api/tts         │
│  - Play audio response                                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend (FastAPI)                                           │
│                                                              │
│  POST /api/stt                                              │
│   → voice.speech_to_text() → Groq Whisper API              │
│   → returns {text, detected_language}                       │
│                                                              │
│  POST /api/chat (existing, unchanged)                       │
│   → LangGraph pipeline (Phases 1-4, unchanged)              │
│   → returns {answer, language, sources, ...}                │
│                                                              │
│  POST /api/tts                                              │
│   → voice.text_to_speech(text, language) → Edge TTS        │
│   → returns audio file (MP3)                                │
└─────────────────────────────────────────────────────────────┘
```

**Key principle**: Voice is pure I/O transformation. The LangGraph RAG pipeline (detect_language → retrieve → generate → etc.) is not modified.

## Implementation Plan

### 1. Backend — Voice Processing Module

**File**: `backend/voice.py`

```python
"""
Phase 5 — Voice I/O

Handles Speech-to-Text (Groq Whisper) and Text-to-Speech (Edge TTS).
Language-aware: detects language from STT, routes to correct TTS voice.
"""

async def speech_to_text(audio_data: bytes) -> dict:
    """
    Transcribe audio using Groq Whisper-large-v3.
    
    Args:
        audio_data: Audio file bytes (WAV, MP3, M4A, etc.)
    
    Returns:
        {
            "text": str,              # Transcribed text
            "language": str,          # Detected language code (e.g. "ar", "en")
            "confidence": float       # Optional: transcription confidence
        }
    
    Raises:
        HTTPException(503): Groq API error or rate limit
    """
    # Implementation:
    # 1. Use Groq client (same GROQ_API_KEY as LLM calls)
    # 2. Call whisper-large-v3 endpoint
    # 3. Extract text + detected language from response
    # 4. Handle rate limits gracefully (return 503 with retry-after)

async def text_to_speech(text: str, language: str) -> bytes:
    """
    Generate speech audio using Edge TTS.
    
    Args:
        text: Text to synthesize
        language: "ar" or "en" (determines voice selection)
    
    Returns:
        Audio bytes (MP3 format)
    
    Raises:
        HTTPException(500): TTS generation failed
    """
    # Implementation:
    # 1. Select voice based on language:
    #    - "ar" or "ar-EG" → "ar-EG-ShakirNeural"
    #    - "en" or fallback → "en-US-GuyNeural"
    # 2. Use edge_tts.Communicate to generate audio
    # 3. Save to temporary file, read bytes, delete temp file
    # 4. Return audio bytes
```

**Dependencies** (`requirements.txt`):
```
edge-tts>=6.1.0          # TTS generation
groq>=0.4.0              # Already exists (Whisper uses same client as LLM)
```

### 2. Backend — API Endpoints

**File**: `backend/main.py` (additions)

```python
from fastapi import File, UploadFile
from fastapi.responses import StreamingResponse
from backend.voice import speech_to_text, text_to_speech

# --- STT Endpoint ---

class STTResponse(BaseModel):
    text: str
    language: str

@app.post("/api/stt", response_model=STTResponse)
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio to text using Groq Whisper.
    
    Accepts: multipart/form-data with 'audio' field (WAV, MP3, M4A, etc.)
    Returns: {text, language}
    
    Rate limit: Groq free tier ~30 req/min (same pool as LLM calls)
    """
    if not audio.content_type.startswith("audio/"):
        raise HTTPException(400, "File must be audio format")
    
    audio_data = await audio.read()
    
    try:
        result = await speech_to_text(audio_data)
        return STTResponse(**result)
    except Exception as e:
        # Log full error, return user-friendly message
        raise HTTPException(503, f"STT service unavailable: {str(e)}")

# --- TTS Endpoint ---

class TTSRequest(BaseModel):
    text: str
    language: str  # "ar" or "en"

@app.post("/api/tts")
async def synthesize_speech(request: TTSRequest):
    """
    Generate speech audio from text using Edge TTS.
    
    Returns: audio/mpeg stream
    """
    if not request.text.strip():
        raise HTTPException(400, "Text cannot be empty")
    
    try:
        audio_bytes = await text_to_speech(request.text, request.language)
        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=response.mp3"}
        )
    except Exception as e:
        raise HTTPException(500, f"TTS generation failed: {str(e)}")
```

**Notes**:
- `/api/stt`: Accepts audio file, returns JSON with transcribed text
- `/api/tts`: Accepts JSON with text + language, returns MP3 audio stream
- Both endpoints handle errors gracefully (rate limits, network errors, invalid input)
- No changes to existing `/api/chat` endpoint

### 3. Frontend — Voice UI

**File**: `frontend/index.html` (additions)

Key additions:
1. **Microphone button** (replaces or supplements text input)
2. **Recording indicator** (visual feedback while recording)
3. **Audio playback controls** (play/pause bot responses)
4. **Permission handling** (graceful fallback if mic access denied)

**HTML structure** (pseudocode):
```html
<!-- Voice input controls -->
<div id="voice-controls">
  <button id="mic-button" aria-label="Record voice message">
    🎤 <!-- Icon changes to ⏺️ when recording -->
  </button>
  <span id="recording-status" style="display:none;">Recording...</span>
</div>

<!-- Audio playback (added to each bot message) -->
<div class="message bot-message">
  <p class="message-text">{{ answer }}</p>
  <button class="play-audio" data-text="{{ answer }}" data-lang="{{ language }}">
    🔊 Play
  </button>
</div>
```

**JavaScript logic** (pseudocode):
```javascript
// 1. Recording
let mediaRecorder;
let audioChunks = [];

micButton.addEventListener('click', async () => {
  if (!mediaRecorder || mediaRecorder.state === 'inactive') {
    // Start recording
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    
    mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      audioChunks = [];
      
      // Send to STT
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      
      const response = await fetch('/api/stt', {
        method: 'POST',
        body: formData
      });
      
      const { text, language } = await response.json();
      
      // Display transcribed text + send to chat
      displayUserMessage(text);
      sendChatMessage(text, sessionId);
    };
    
    mediaRecorder.start();
    micButton.textContent = '⏺️'; // Recording indicator
  } else {
    // Stop recording
    mediaRecorder.stop();
    micButton.textContent = '🎤';
  }
});

// 2. Playback
document.addEventListener('click', async (e) => {
  if (e.target.classList.contains('play-audio')) {
    const text = e.target.dataset.text;
    const language = e.target.dataset.lang;
    
    // Request TTS
    const response = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, language })
    });
    
    const audioBlob = await response.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    
    const audio = new Audio(audioUrl);
    audio.play();
    
    // Cleanup after playback
    audio.onended = () => URL.revokeObjectURL(audioUrl);
  }
});
```

**UX considerations**:
- Show loading spinner during STT/TTS processing
- Display transcribed text before sending to chat (user can edit if STT made a mistake)
- Auto-play TTS responses (optional, with toggle)
- Handle mic permission denial gracefully (show message, keep text input available)

### 4. Environment Variables

**File**: `.env`

No new keys needed:
- `GROQ_API_KEY`: Already exists (used for both LLM and Whisper)
- Edge TTS: No API key required (free, open-access)

### 5. Testing Strategy

**Backend tests** (`tests/test_voice.py`):
```python
# 1. STT with English audio
async def test_stt_english():
    # Load sample WAV file
    # POST to /api/stt
    # Assert: text is transcribed, language is "en"

# 2. STT with Arabic audio
async def test_stt_arabic():
    # Load sample Arabic WAV
    # POST to /api/stt
    # Assert: text is transcribed, language is "ar"

# 3. TTS English
async def test_tts_english():
    # POST to /api/tts with {text: "Hello", language: "en"}
    # Assert: response is audio/mpeg, non-empty

# 4. TTS Arabic
async def test_tts_arabic():
    # POST to /api/tts with {text: "مرحبا", language: "ar"}
    # Assert: response is audio/mpeg, non-empty

# 5. Error handling
async def test_stt_invalid_file():
    # POST non-audio file to /api/stt
    # Assert: 400 error

async def test_tts_empty_text():
    # POST empty text to /api/tts
    # Assert: 400 error
```

**Manual testing checklist**:
- [ ] Record English question, verify correct transcription
- [ ] Record Arabic question, verify correct transcription
- [ ] Verify TTS plays correct voice (English vs Arabic)
- [ ] Test full voice loop (speak → transcribe → chat → TTS → hear response)
- [ ] Test with mic permission denied (should show error, text input still works)
- [ ] Test on mobile browser (iOS Safari, Android Chrome)
- [ ] Verify Groq rate limits are handled gracefully (show user-friendly error)

## Deployment Notes

**Backend** (Render):
- No new environment variables needed
- Edge TTS may require `ffmpeg` system dependency (check Render buildpack)
- If `ffmpeg` missing, add to `render.yaml` or use Render's `nativeRuntimeDeps`

**Frontend** (Vercel):
- No changes to build process
- MediaRecorder API works in all modern browsers (Chrome, Firefox, Safari 14.1+)
- HTTPS required for `getUserMedia` (Vercel provides this automatically)

## Rate Limit Considerations

**Groq free tier** (as of 2026-09-25):
- ~30 requests/min across all endpoints (LLM + Whisper share same pool)
- Voice I/O adds 2 extra API calls per interaction (1 STT + 1 LLM)
- TTS (Edge TTS) has no rate limit (client-side library, no API)

**Mitigation**:
- Display user-friendly rate limit message ("I'm getting a lot of questions right now, please try again in a moment")
- Consider caching common questions (already implemented in Phase 2 cache node)
- TTS happens after answer is generated, so rate limits only affect STT/LLM, not playback

## Security Notes

**Audio upload**:
- Validate `Content-Type` header (must start with `audio/`)
- Limit file size (e.g., max 10MB to prevent abuse)
- Do not persist audio files (process in-memory only)

**TTS**:
- Sanitize text input (Edge TTS should handle this, but validate max length ~5000 chars to prevent abuse)
- No untrusted code execution (Edge TTS generates audio, doesn't run arbitrary commands)

## Files Changed Summary

**New files**:
- `backend/voice.py` (STT + TTS functions)
- `tests/test_voice.py` (unit tests)
- `docs/PHASE5_VOICE_SETUP.md` (this file)

**Modified files**:
- `backend/main.py` (add `/api/stt` and `/api/tts` endpoints)
- `frontend/index.html` (add voice UI controls + recording/playback logic)
- `requirements.txt` (add `edge-tts`)
- `TASKS.md` (mark Phase 5 as complete)

**NOT changed**:
- Database schema (no changes needed)
- `backend/graph.py` (LangGraph pipeline unchanged)
- `backend/generation.py`, `backend/retrieval.py` (unchanged)
- `.env` (no new keys needed)

## References

- [Groq Whisper API docs](https://console.groq.com/docs/speech-text)
- [Edge TTS Python library](https://github.com/rany2/edge-tts)
- [MDN MediaRecorder API](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder)
