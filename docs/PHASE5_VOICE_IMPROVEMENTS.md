# Phase 5 Voice Improvements — UX Issues & Solutions

> Issues discovered during initial testing (2026-09-25)
> This document tracks voice-specific UX problems and their solutions

## Issue 1: Long Responses Are Exhausting to Listen To

**Problem**: RAG-generated answers are optimized for reading (detailed, comprehensive), not listening. A 500-word response about a project is fine to read but terrible to hear.

**User Impact**: 
- Voice responses take 30-60+ seconds to play
- User loses attention midway
- Information overload in audio form

### Solutions (Pick One)

#### Option A: Voice-Optimized Generation Prompt (Recommended)
Add a `voice_mode` flag to the generation system:

```python
# In backend/generation.py or backend/graph.py
def _build_system_prompt(language: str, voice_mode: bool = False) -> str:
    if voice_mode:
        instruction = "Keep responses SHORT and conversational (2-3 sentences max). Prioritize key facts only."
    else:
        instruction = "Be thorough and comprehensive."
    # ... rest of prompt
```

**Pros**: 
- Clean separation between text and voice responses
- Users get appropriate detail level per medium

**Cons**: 
- Requires backend changes
- May sacrifice detail in voice responses

**Implementation**:
1. Add `voice_mode: bool` parameter to generation functions
2. Modify system prompt based on flag
3. Frontend sends `voice_mode=true` when user spoke (vs typed)

---

#### Option B: Post-Generation Summarization
After generating the full answer, summarize it before TTS:

```python
# In backend/voice.py
async def text_to_speech(text: str, language: str, summarize: bool = True) -> bytes:
    if summarize and len(text) > 300:
        # Use Groq to condense the text
        summary = await summarize_for_voice(text, language)
        text = summary
    # ... rest of TTS logic
```

**Pros**: 
- Preserves full text answer for display
- Audio gets condensed version

**Cons**: 
- Extra LLM call = slower + more tokens
- Summary quality depends on LLM

---

#### Option C: Client-Side "Quick Summary" Toggle (Easiest)
Let user choose:

```html
<!-- In frontend -->
<button class="play-audio-btn" data-mode="full">🔊 Play Full</button>
<button class="play-audio-btn" data-mode="summary">⚡ Quick Summary</button>
```

**Pros**: 
- No backend changes
- User controls verbosity

**Cons**: 
- User has to make a choice every time
- Summary still needs implementation

---

**Recommendation**: Start with **Option A** (voice-optimized prompt). It's the cleanest architectural solution.

---

## Issue 2: Markdown & Emojis Sound Terrible in TTS

**Problem**: TTS reads markdown syntax and emoji descriptions literally:
- `**bold**` → "asterisk asterisk bold asterisk asterisk"
- `# Heading` → "hashtag Heading"
- `🎓` → "graduation cap emoji"
- `- Bullet point` → "dash Bullet point"

**User Impact**: Audio is cluttered with nonsense words

### Solution: Strip Markdown/Emojis Before TTS

Add a text cleaning function in `backend/voice.py`:

```python
import re

def clean_text_for_speech(text: str) -> str:
    """
    Strip markdown formatting and emojis to make text TTS-friendly.
    
    Removes:
    - Markdown bold/italic (* ** _ __)
    - Headings (# ## ###)
    - Bullet points (- *)
    - Links [text](url) → text only
    - Emojis (Unicode range)
    - Code blocks (``` ```)
    """
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)
    
    # Remove markdown links [text](url) → keep text only
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove markdown emphasis (bold/italic)
    text = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', text)
    
    # Remove headings
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove bullet points
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    
    # Remove emojis (Unicode ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", 
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text

# Update text_to_speech to use this
async def text_to_speech(text: str, language: str) -> bytes:
    # ... validation ...
    
    # Clean text for speech
    clean_text = clean_text_for_speech(text)
    
    # Select voice and generate
    voice = TTS_VOICES.get(language, TTS_VOICES["en"])
    communicate = edge_tts.Communicate(clean_text, voice)
    # ... rest of logic
```

**Implementation Steps**:
1. Add `clean_text_for_speech()` function to `backend/voice.py`
2. Call it inside `text_to_speech()` before generating audio
3. Test with markdown-heavy responses

**Testing**:
- Input: `"I built **three projects**: \n- KYC System 🎓\n- Social Media Tool"`
- Expected: `"I built three projects: KYC System Social Media Tool"`

---

## Issue 3: Code-Switching (Arabic + English Mix) Sounds Bad

**Problem**: Technical conversations naturally mix languages:
- Arabic: "انا عملت project using FastAPI و PostgreSQL"
- English: "I used FastAPI and PostgreSQL for the backend"

Arabic TTS voice (ar-EG-ShakirNeural) struggles with English words → sounds robotic/mispronounced.

**User Impact**: 
- Audio quality is poor
- Comprehension suffers

### Root Cause
Edge TTS voices are **monolingual**:
- `ar-EG-ShakirNeural` is trained on Arabic phonetics only
- When it encounters "FastAPI", it tries to pronounce it with Arabic phonemes → sounds wrong

### Solutions (Ranked by Feasibility)

#### Option A: Document as Known Limitation (Easiest)
Accept that free TTS has this limitation. Update docs:

```markdown
**Known Limitation**: Arabic voice responses containing English technical terms 
(e.g., "FastAPI", "PostgreSQL") may sound unnatural. For best audio quality, 
ask questions in English when discussing technical topics.
```

**Pros**: 
- Zero implementation effort
- Free TTS will always have trade-offs

**Cons**: 
- Poor UX for Arabic speakers asking about tech

---

#### Option B: Use English TTS for Tech-Heavy Responses
Detect if response contains many English words → force English TTS even if user spoke Arabic:

```python
def should_use_english_tts(text: str, detected_language: str) -> bool:
    """
    If Arabic text has >30% English words, use English TTS instead.
    """
    if detected_language != "ar":
        return detected_language == "en"
    
    # Count English words (simple heuristic: Latin alphabet)
    words = text.split()
    english_words = [w for w in words if re.match(r'^[a-zA-Z]+', w)]
    
    english_ratio = len(english_words) / len(words)
    return english_ratio > 0.3  # If >30% English, use English TTS
```

**Pros**: 
- Automatically adapts to content
- English TTS handles English terms better

**Cons**: 
- User asked in Arabic, gets English audio (confusing?)
- Heuristic may misfire

---

#### Option C: Find a Bilingual TTS Model (Hard, Maybe Impossible for Free)

Research free/open bilingual Arabic-English TTS models:

**Candidates** (need verification):
1. **Coqui TTS** (open-source, self-hosted)
   - Has multilingual models
   - Requires local setup
   - Free but needs GPU for real-time

2. **Azure Cognitive Services** (paid, but has free tier)
   - Bilingual voices exist (e.g., `en-US-AriaNeural` can handle some Arabic)
   - Free tier: 500K characters/month
   - Better quality than Edge TTS

3. **Google Cloud TTS** (paid, has free tier)
   - WaveNet voices handle code-switching better
   - Free tier: 1M characters/month (TTS Standard), 100K (WaveNet)

**Problem**: All better options require API keys or local setup → adds complexity

---

#### Option D: Pre-process Text to Help TTS (Compromise)

For Arabic responses with English terms, **transliterate English words to Arabic phonetics**:

Example:
- Original: "استخدمت FastAPI و PostgreSQL"
- Pre-processed: "استخدمت فاست-ايه-بي-آي و بوست-جريه-اس-كيو-ال"

**Pros**: 
- Edge TTS can pronounce Arabic phonetics correctly
- No new APIs needed

**Cons**: 
- Transliteration is hard (need a dictionary)
- May sound unnatural ("فاست-ايه-بي-آي" is awkward)

---

**Recommendation**: Start with **Option A** (document limitation). If UX is too poor, implement **Option B** (auto-detect code-switching and use English TTS).

---

## Summary of Recommended Actions

| Issue | Solution | Priority | Effort |
|-------|----------|----------|--------|
| Long responses | Voice-optimized prompt (Option A) | High | Medium |
| Markdown in TTS | Clean text before TTS | High | Low |
| Code-switching | Document limitation (Option A) | Medium | Zero |

**Next Steps**:
1. Implement markdown/emoji stripping (quick win)
2. Add voice-optimized generation mode
3. Test with real Arabic + English mixed queries
4. Decide if code-switching UX is acceptable or needs Option B

---

## Implementation Checklist

- [ ] Add `clean_text_for_speech()` to `backend/voice.py`
- [ ] Update `text_to_speech()` to clean text before TTS
- [ ] Add `voice_mode` parameter to generation system
- [ ] Modify system prompt for voice vs text responses
- [ ] Test with markdown-heavy responses
- [ ] Test with Arabic + English mixed responses
- [ ] Update frontend to pass `voice_mode` flag when user speaks
- [ ] Document known limitations in README
