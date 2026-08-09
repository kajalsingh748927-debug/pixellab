"""
modules/transcribe_engine.py
─────────────────────────────────────────────────────────────────────────────
Audio Transcription Engine for Pixelab — Custom Audio Upload Mode.

Accepts a user-uploaded audio file (MP3 / WAV / M4A / OGG) and returns:
  - full_text       : str   — complete narration transcription
  - word_timestamps : list  — [{word, start, end}, ...] in seconds
  - total_duration  : float — audio length in seconds

Strategy (3-tier):
  1. ElevenLabs Speech-to-Text API   — ultra-accurate, word-level timestamps
  2. openai-whisper (local, free)    — accurate, no API key needed
  3. Linear interpolation fallback   — always works, no dependencies

Usage:
    from modules.transcribe_engine import transcribe_audio
    result = transcribe_audio("path/to/audio.mp3")
    # result = {"full_text": "...", "word_timestamps": [...], "total_duration": 42.3}
─────────────────────────────────────────────────────────────────────────────
"""
import os
import requests


def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", errors="ignore").decode("ascii"))
        except Exception:
            pass


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_audio_duration(audio_path: str) -> float:
    """Returns the duration of an audio file in seconds using moviepy."""
    try:
        from moviepy import AudioFileClip
        clip = AudioFileClip(audio_path)
        dur = float(clip.duration)
        clip.close()
        return dur
    except Exception:
        pass
    # Fallback via wave (WAV only)
    try:
        import wave
        with wave.open(audio_path, "rb") as w:
            return float(w.getnframes()) / float(w.getframerate())
    except Exception:
        pass
    return 10.0


def _linear_timestamps(text: str, total_duration: float) -> list:
    """
    Distributes word timestamps evenly across total_duration.
    Used when Whisper is unavailable.
    """
    words = [w for w in text.split() if w]
    n = len(words)
    if n == 0 or total_duration <= 0:
        return []
    per_word = total_duration / n
    return [
        {
            "word":  word,
            "start": round(i * per_word, 3),
            "end":   round((i + 1) * per_word - 0.02, 3),
        }
        for i, word in enumerate(words)
    ]


# ── ElevenLabs Speech-to-Text ────────────────────────────────────────────────

def _transcribe_with_elevenlabs(audio_path: str) -> dict | None:
    """
    Uses the ElevenLabs /speech-to-text API to transcribe the audio file.
    Returns {"full_text", "word_timestamps", "total_duration"} or None if
    the API key is missing or the call fails.

    ElevenLabs STT supports: MP3, WAV, M4A, OGG, FLAC, WebM, MP4.
    Returns character-level alignment which is reconstructed into words.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        return None  # No key — skip silently, fall through to Whisper

    safe_print("ElevenLabs STT: transcribing uploaded audio...")

    url = "https://api.elevenlabs.io/v1/speech-to-text"
    headers = {"xi-api-key": api_key}

    try:
        ext = os.path.splitext(audio_path)[-1].lower().lstrip(".")
        mime_map = {
            "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
            "ogg": "audio/ogg", "flac": "audio/flac", "aac": "audio/aac",
            "webm": "audio/webm", "mp4": "audio/mp4",
        }
        mime_type = mime_map.get(ext, "audio/mpeg")

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, mime_type)}
            data  = {
                "model_id":             "scribe_v1",
                "timestamps_granularity": "word",
                "diarize":              "false",
            }
            res = requests.post(url, headers=headers, files=files, data=data, timeout=120)

        if res.status_code != 200:
            safe_print(f"ElevenLabs STT API notice ({res.status_code}): {res.text[:150]}")
            return None

        data_out = res.json()

        # Extract text
        full_text = data_out.get("text", "").strip()

        # Extract word-level timestamps
        word_timestamps = []
        for w in data_out.get("words", []):
            word = w.get("text", "").strip()
            if not word:
                continue
            word_timestamps.append({
                "word":  word,
                "start": round(float(w.get("start", 0)), 3),
                "end":   round(float(w.get("end", 0)), 3),
            })

        total_duration = _get_audio_duration(audio_path)
        if total_duration <= 0 and word_timestamps:
            total_duration = word_timestamps[-1]["end"] + 0.1

        # If word timestamps missing but text is good, use linear
        if full_text and not word_timestamps:
            safe_print("ElevenLabs STT: no word timestamps returned - using linear interpolation.")
            word_timestamps = _linear_timestamps(full_text, total_duration)

        safe_print(
            f"ElevenLabs STT: {len(word_timestamps)} words | {total_duration:.1f}s"
        )
        return {
            "full_text":       full_text,
            "word_timestamps": word_timestamps,
            "total_duration":  float(total_duration),
        }

    except Exception as e:
        safe_print(f"ElevenLabs STT error: {str(e).encode('ascii', errors='replace').decode('ascii')}")
        return None


# ── Groq Whisper Transcription (cloud, zero local RAM) ───────────────────────

def _transcribe_with_groq_whisper(audio_path: str) -> dict | None:
    """
    Uses Groq's free Whisper API (whisper-large-v3) for transcription.
    Runs on Groq's servers — uses zero local RAM. Perfect for Render free tier.
    Returns {full_text, word_timestamps, total_duration} or None on failure.
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return None

    safe_print("🎙️ Groq Whisper: transcribing audio...")

    try:
        import json

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}

        ext = os.path.splitext(audio_path)[-1].lower().lstrip(".")
        mime_map = {
            "mp3": "audio/mpeg", "wav": "audio/wav", "m4a": "audio/mp4",
            "ogg": "audio/ogg", "flac": "audio/flac", "webm": "audio/webm",
            "mp4": "audio/mp4",
        }
        mime_type = mime_map.get(ext, "audio/mpeg")

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, mime_type)}
            data = {
                "model": "whisper-large-v3",
                "response_format": "verbose_json",
                "timestamp_granularities[]": "word",
            }
            res = requests.post(url, headers=headers, files=files, data=data, timeout=120)

        if res.status_code != 200:
            safe_print(f"Groq Whisper error ({res.status_code}): {res.text[:200]}")
            return None

        result = res.json()
        full_text = result.get("text", "").strip()
        total_duration = _get_audio_duration(audio_path)

        # Extract word-level timestamps
        word_timestamps = []
        for w in result.get("words", []):
            word = w.get("word", "").strip()
            if word:
                word_timestamps.append({
                    "word":  word,
                    "start": round(float(w.get("start", 0)), 3),
                    "end":   round(float(w.get("end", 0)), 3),
                })

        if full_text and not word_timestamps:
            safe_print("Groq Whisper: no word timestamps — using linear interpolation.")
            word_timestamps = _linear_timestamps(full_text, total_duration)

        safe_print(f"✅ Groq Whisper: {len(word_timestamps)} words | {total_duration:.1f}s")
        return {
            "full_text":       full_text,
            "word_timestamps": word_timestamps,
            "total_duration":  total_duration,
        }

    except Exception as e:
        safe_print(f"Groq Whisper error: {e}")
        return None


# ── Local Whisper Transcription (fallback if Groq unavailable) ───────────────

def _transcribe_with_whisper(audio_path: str) -> dict | None:
    """
    Runs openai-whisper locally. Only used if Groq is unavailable.
    Returns {full_text, word_timestamps, total_duration} or None.
    """
    try:
        import whisper  # noqa: F401
    except ImportError:
        safe_print("⚠️  openai-whisper not installed — skipping local Whisper.")
        return None

    # Ensure FFmpeg directory is in Windows system PATH for Whisper subprocesses
    try:
        import imageio_ffmpeg
        ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass

    try:
        safe_print("🎙️ Loading Whisper base model (74 MB, first run downloads it)...")
        model = whisper.load_model("base")

        safe_print(f"🔍 Transcribing: {os.path.basename(audio_path)} ...")
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            language=None,   # Auto-detect language
            verbose=False,
        )

        # Extract word-level timestamps from segments
        word_timestamps = []
        for seg in result.get("segments", []):
            for w in seg.get("words", []):
                word = w.get("word", "").strip()
                if word:
                    word_timestamps.append({
                        "word":  word,
                        "start": round(float(w.get("start", 0)), 3),
                        "end":   round(float(w.get("end", 0)), 3),
                    })

        full_text = result.get("text", "").strip()
        total_duration = _get_audio_duration(audio_path)

        # If duration wasn't found from moviepy, use last word end time
        if total_duration <= 0 and word_timestamps:
            total_duration = word_timestamps[-1]["end"] + 0.1

        # If Whisper gave us text but no word timestamps (can happen with
        # some audio formats or very short clips), fall back to linear.
        if full_text and not word_timestamps:
            safe_print("⚠️ Whisper returned text but no word timestamps — using linear interpolation.")
            word_timestamps = _linear_timestamps(full_text, total_duration)

        safe_print(f"✅ Whisper transcribed {len(word_timestamps)} words | {total_duration:.1f}s total")

        return {
            "full_text":       full_text,
            "word_timestamps": word_timestamps,
            "total_duration":  total_duration,
        }

    except Exception as e:
        safe_print(f"⚠️ Whisper transcription error: {e}")
        return None


# ── Master Function ───────────────────────────────────────────────────────────

def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribes a user-uploaded audio file and returns word-level timestamps.

    Parameters
    ----------
    audio_path : str
        Absolute path to the audio file (MP3, WAV, M4A, OGG, FLAC, etc.)

    Returns
    -------
    dict with keys:
        "full_text"       : str   — complete transcription text
        "word_timestamps" : list  — [{word, start, end}, ...]  (times in seconds)
        "total_duration"  : float — audio length in seconds
        "method"          : str   — "elevenlabs" | "whisper" | "whisper_linear" | "linear_fallback"
    """
    if not os.path.exists(audio_path):
        safe_print(f"Audio file not found: {audio_path}")
        return {"full_text": "", "word_timestamps": [], "total_duration": 0.0, "method": "none"}

    # ── Strategy 1: ElevenLabs STT (if API key is set) ───────────────────────
    result = _transcribe_with_elevenlabs(audio_path)
    if result and result.get("full_text"):
        result["method"] = "elevenlabs"
        return result

    # ── Strategy 2: Groq Whisper API (free, cloud, zero local RAM) ───────────
    result = _transcribe_with_groq_whisper(audio_path)
    if result and result.get("full_text"):
        result["method"] = "groq_whisper"
        return result

    # ── Strategy 3: Local Whisper (if installed) ──────────────────────────────
    result = _transcribe_with_whisper(audio_path)
    if result:
        method = "whisper"
        if result["full_text"] and not result["word_timestamps"]:
            result["word_timestamps"] = _linear_timestamps(
                result["full_text"], result["total_duration"]
            )
            method = "whisper_linear"
        result["method"] = method
        if result["full_text"]:
            return result

    # ── Strategy 4: Linear fallback (nothing worked) ─────────────────────────
    safe_print("Using linear timestamp interpolation fallback...")
    total_duration = _get_audio_duration(audio_path)

    full_text = ""
    if result and result.get("full_text"):
        full_text = result["full_text"]

    if not full_text:
        safe_print(
            "Could not transcribe audio. Set GROQ_API_KEY or ELEVENLABS_API_KEY for transcription."
        )
        return {
            "full_text":       "",
            "word_timestamps": [],
            "total_duration":  total_duration,
            "method":          "none",
        }

    word_timestamps = _linear_timestamps(full_text, total_duration)
    return {
        "full_text":       full_text,
        "word_timestamps": word_timestamps,
        "total_duration":  total_duration,
        "method":          "linear_fallback",
    }
