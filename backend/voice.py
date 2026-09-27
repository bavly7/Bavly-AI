"""
Phase 5 — Voice I/O

Handles Speech-to-Text (Groq Whisper) and Text-to-Speech (Edge TTS).
Language-aware: detects language from STT, routes to correct TTS voice.
"""

import os
import re
import tempfile
from io import BytesIO

import edge_tts
from dotenv import load_dotenv
from fastapi import HTTPException
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.environ["GROQ_API_KEY_VOICE"]
groq_client = Groq(api_key=GROQ_API_KEY)

# Voice selections per language (TASKS.md decisions)
TTS_VOICES = {
    "ar": "ar-EG-ShakirNeural",      # Egyptian Arabic male voice
    "ar-EG": "ar-EG-ShakirNeural",
    "en": "en-US-GuyNeural",          # English male voice
}


def clean_text_for_speech(text: str) -> str:
    """
    Clean text for TTS by removing markdown formatting and emojis.

    Removes:
    - Markdown bold/italic (**, __, *, _)
    - Headings (# ## ###)
    - Bullet points (-, *)
    - Links [text](url) → keep text only
    - Code blocks (``` ```)
    - Emojis (Unicode ranges)
    """
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]+`', '', text)

    # Remove markdown links [text](url) → keep text only
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove markdown emphasis (bold/italic)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
    text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
    text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
    text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_

    # Remove headings
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)

    # Remove bullet points at start of lines
    text = re.sub(r'^\s*[-*•]\s+', '', text, flags=re.MULTILINE)

    # Remove emojis (comprehensive Unicode ranges)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # extended symbols
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)

    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
    text = re.sub(r' {2,}', ' ', text)       # Max 1 space
    text = text.strip()

    return text


# def detect_language_for_tts(text: str, declared_language: str) -> str:
#     """
#     Detect best TTS voice based on text content.

#     UPDATED APPROACH:
#     - If text is primarily Arabic (has Arabic chars) → use Arabic TTS
#     - Arabic TTS will struggle with English words but at least reads Arabic
#     - Only use English TTS if text has NO Arabic at all

#     Args:
#         text: The text to be spoken
#         declared_language: Language from backend ("ar" or "en")

#     Returns:
#         Language code for TTS voice selection ("ar" or "en")
#     """
#     # If declared language is English, use English
#     if not declared_language.startswith("ar"):
#         return "en"

#     # Check if text contains ANY Arabic characters
#     has_arabic = bool(re.search(r'[؀-ۿ]', text))

#     # If text has Arabic characters, use Arabic TTS
#     # Even if there are English words, Arabic TTS will try to read them
#     # Better to have poorly-pronounced English than skipped Arabic
#     if has_arabic:
#         return "ar"

#     # No Arabic characters at all → use English TTS
#     return "en"

def detect_language_for_tts(text: str, declared_language: str) -> str:
    if bool(re.search(r'[؀-ۿ]', text)):
        return "ar"
    return "en"

async def speech_to_text(audio_data: bytes, filename: str = "audio.webm") -> dict:
    """
    Transcribe audio using Groq Whisper-large-v3.

    Args:
        audio_data: Audio file bytes (WebM, WAV, MP3, M4A, etc.)
        filename: Original filename (used for content type detection)

    Returns:
        {
            "text": str,              # Transcribed text
            "language": str,          # Detected language code (e.g. "ar", "en")
        }

    Raises:
        HTTPException(503): Groq API error or rate limit
        HTTPException(400): Invalid audio format
    """
    try:
        # Create a file-like object from bytes
        # Groq API expects a file with a name attribute
        audio_file = BytesIO(audio_data)
        audio_file.name = filename

        # Call Groq Whisper API
        transcription = groq_client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=audio_file,
            response_format="verbose_json",  # Get language info
        )

        return {
            "text": transcription.text.strip(),
            "language": transcription.language,  # ISO 639-1 code: "ar", "en", etc.
        }

    except Exception as e:
        error_msg = str(e)

        # Handle common error cases
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Speech recognition service is busy. Please try again in a moment."
            )
        elif "invalid" in error_msg.lower() or "format" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid audio format. Supported formats: WAV, MP3, M4A, WebM"
            )
        else:
            # Generic error
            raise HTTPException(
                status_code=503,
                detail=f"Speech recognition failed: {error_msg}"
            )


async def text_to_speech(text: str, language: str) -> bytes:
    """
    Generate speech audio using Edge TTS.

    Args:
        text: Text to synthesize (will be cleaned automatically)
        language: "ar", "ar-EG", "en", or other supported code

    Returns:
        Audio bytes (MP3 format)

    Raises:
        HTTPException(400): Empty text or text too long
        HTTPException(500): TTS generation failed
    """
    # Validation
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    # Clean text for TTS (remove markdown, emojis)
    clean_text = clean_text_for_speech(text)

    if not clean_text.strip():
        raise HTTPException(status_code=400, detail="Text is empty after cleaning")

    if len(clean_text) > 5000:
        raise HTTPException(
            status_code=400,
            detail="Text too long (max 5000 characters)"
        )

    # Detect best language for TTS (handles code-switching)
    tts_language = detect_language_for_tts(clean_text, language)

    # Select voice based on detected language
    voice = TTS_VOICES.get(tts_language, TTS_VOICES["en"])  # Default to English

    try:
        # Generate audio using Edge TTS
        communicate = edge_tts.Communicate(clean_text, voice)

        # Save to temporary file (Edge TTS writes to file)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name

        await communicate.save(tmp_path)

        # Read audio bytes
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        # Clean up temp file
        os.unlink(tmp_path)

        return audio_bytes

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Text-to-speech generation failed: {str(e)}"
        )
