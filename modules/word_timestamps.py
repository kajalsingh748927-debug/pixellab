"""
modules/word_timestamps.py
─────────────────────────────────────────────────────────────────────────────
Word-Level Timestamp Engine for Pixelab.

Extracts millisecond-accurate word start/end times from audio so subtitles
can highlight exactly the right word at each moment (Hormozi / MrBeast style).

Strategy (two-tier):
  1. ElevenLabs /with-timestamps API  →  character-level, reconstructed to words
  2. Whisper (openai-whisper) local fallback → word-level via forced alignment

Returns: List[dict] — [{word, start, end}, ...] (times in seconds)
─────────────────────────────────────────────────────────────────────────────
"""
import os
import json
import base64
import tempfile
import requests


def safe_print(msg):
    try:
        print(msg)
    except Exception:
        pass


# ── ElevenLabs Timestamps ────────────────────────────────────

ELEVENLABS_VOICES = {
    "[ElevenLabs] George (Storyteller)": "JBFqnCBsd6RMkjVDRZzb",
    "[ElevenLabs] Adam (Dominant & Firm)": "pNInz6obpgDQGcFmaJgB",
    "[ElevenLabs] Sarah (Confident Female)": "EXAVITQu4vr4xnSDxMaL",
    "[ElevenLabs] Charlie (Deep & Energetic)": "IKne3meq5aSn9XLyUdCD",
    "[ElevenLabs] Brian (Deep & Comforting)": "nPczCjzI2devNBz1zQrb",
    "[ElevenLabs] Alice (Engaging Educator)": "Xb7hH8MSUJpSbSDYk0k2",
    "[ElevenLabs] Liam (Social Media Creator)": "TX3LPaxmHKxFdv7VOQHJ",
    "[ElevenLabs] Viraj (Rich Indian Male)": "3AMU7jXQuQa3oRvRqUmb",
}


def _chars_to_words(characters: list, char_starts: list, char_ends: list) -> list:
    """
    Converts ElevenLabs character-level alignment to word-level timestamps.
    Groups consecutive non-space characters into words.
    """
    words = []
    current_word = ""
    word_start   = None
    word_end     = None

    for i, char in enumerate(characters):
        if char == " " or char == "":
            if current_word:
                words.append({
                    "word":  current_word,
                    "start": word_start,
                    "end":   word_end,
                })
                current_word = ""
                word_start   = None
                word_end     = None
        else:
            if word_start is None:
                word_start = char_starts[i]
            word_end     = char_ends[i]
            current_word += char

    # Flush last word
    if current_word:
        words.append({
            "word":  current_word,
            "start": word_start,
            "end":   word_end,
        })

    return words


def get_elevenlabs_timestamps(text: str, voice: str, api_key: str,
                               output_audio_path: str = None) -> tuple[list, bool]:
    """
    Calls ElevenLabs /with-timestamps endpoint.
    Returns (word_timestamps, success).
    If output_audio_path is given, also saves the audio MP3 there.
    """
    voice_id = ELEVENLABS_VOICES.get(voice, "JBFqnCBsd6RMkjVDRZzb")
    url      = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    headers  = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload  = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=35)
        if res.status_code != 200:
            safe_print(f"⚠️ ElevenLabs timestamps API: {res.status_code}")
            return [], False

        data       = res.json()
        audio_b64  = data.get("audio_base64", "")
        alignment  = data.get("alignment", {})

        chars        = alignment.get("characters", [])
        char_starts  = alignment.get("character_start_times_seconds", [])
        char_ends    = alignment.get("character_end_times_seconds", [])

        # Save audio if path given
        if output_audio_path and audio_b64:
            audio_bytes = base64.b64decode(audio_b64)
            with open(output_audio_path, "wb") as f:
                f.write(audio_bytes)

        # Convert character → word timestamps
        word_ts = _chars_to_words(chars, char_starts, char_ends)
        safe_print(f"✅ ElevenLabs timestamps: {len(word_ts)} words synced")
        return word_ts, True

    except Exception as e:
        safe_print(f"⚠️ ElevenLabs timestamps exception: {e}")
        return [], False


# ── Whisper Local Fallback ────────────────────────────────────

def get_whisper_timestamps(audio_path: str) -> list:
    """
    Uses openai-whisper to extract word-level timestamps locally (free, offline).
    Requires: pip install openai-whisper
    Returns list of {word, start, end} or [] if whisper not available.
    """
    try:
        import whisper  # noqa: F401
        model  = whisper.load_model("base")  # 74MB, fast
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            language="en",
            verbose=False,
        )
        word_ts = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                word_ts.append({
                    "word":  w["word"].strip(),
                    "start": w["start"],
                    "end":   w["end"],
                })
        safe_print(f"✅ Whisper timestamps: {len(word_ts)} words synced")
        return word_ts
    except ImportError:
        safe_print("⚠️ openai-whisper not installed — using linear interpolation fallback")
        return []
    except Exception as e:
        safe_print(f"⚠️ Whisper error: {e}")
        return []


# ── Linear Interpolation Fallback ────────────────────────────

def get_linear_timestamps(text: str, audio_duration: float) -> list:
    """
    Fallback: evenly distributes word timestamps across the audio duration.
    Not accurate but ensures subtitles still highlight word-by-word.
    """
    words    = [w for w in text.split() if w]
    n        = len(words)
    if n == 0 or audio_duration <= 0:
        return []

    per_word = audio_duration / n
    return [
        {
            "word":  word,
            "start": round(i * per_word, 3),
            "end":   round((i + 1) * per_word - 0.02, 3),
        }
        for i, word in enumerate(words)
    ]


# ── Master function ───────────────────────────────────────────

def get_word_timestamps(text: str, voice: str, audio_path: str,
                         audio_duration: float) -> list:
    """
    Gets word-level timestamps using the best available method:
      1. ElevenLabs /with-timestamps (if ElevenLabs voice + API key)
      2. Whisper local (if installed)
      3. Linear interpolation (always works)

    Returns List[{word, start, end}] in seconds.
    """
    from modules.cache_manager import get_cached_timestamps, set_cached_timestamps

    # Check cache first
    cached = get_cached_timestamps(text, voice)
    if cached:
        safe_print(f"  📦 Word timestamps from cache ({len(cached)} words)")
        return cached

    api_key   = os.environ.get("ELEVENLABS_API_KEY", "")
    is_eleven = voice in ELEVENLABS_VOICES or voice.startswith("[ElevenLabs]")

    # Strategy 1: ElevenLabs
    if is_eleven and api_key and os.path.exists(audio_path):
        # We already have audio from tts_engine; call timestamps-only if audio missing
        if os.path.getsize(audio_path) < 100:
            ts, ok = get_elevenlabs_timestamps(text, voice, api_key, audio_path)
        else:
            # Audio already exists — use lightweight alignment call
            ts, ok = get_elevenlabs_timestamps(text, voice, api_key)
        if ok and ts:
            set_cached_timestamps(text, voice, ts)
            return ts

    # Strategy 2: Whisper
    if os.path.exists(audio_path):
        ts = get_whisper_timestamps(audio_path)
        if ts:
            set_cached_timestamps(text, voice, ts)
            return ts

    # Strategy 3: Linear fallback
    safe_print("  ⚡ Using linear timestamp interpolation")
    ts = get_linear_timestamps(text, audio_duration)
    set_cached_timestamps(text, voice, ts)
    return ts
