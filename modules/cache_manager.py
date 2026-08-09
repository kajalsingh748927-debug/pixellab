"""
modules/cache_manager.py
─────────────────────────────────────────────────────────────────────────────
Smart Caching System for Pixelab.

Caches:
  • TTS audio files  (7-day TTL)  — same narration+voice = skip ElevenLabs call
  • Stock video files (24-hour TTL) — same query = skip download
  • Word timestamps   (7-day TTL)  — same audio = skip re-alignment

Uses diskcache for disk-backed key-value storage with automatic expiry.
─────────────────────────────────────────────────────────────────────────────
"""
import os
import hashlib
import shutil
import diskcache

# Cache directory — lives next to the project root
_BASE_DIR  = os.path.join(os.path.dirname(__file__), "..", "cache")
_CACHE_DIR = os.path.abspath(_BASE_DIR)
os.makedirs(_CACHE_DIR, exist_ok=True)

# Persistent files cache dir (actual media files, not just paths)
_FILES_DIR = os.path.join(_CACHE_DIR, "files")
os.makedirs(_FILES_DIR, exist_ok=True)

# DiskCache instance — 3 GB max
_cache = diskcache.Cache(_CACHE_DIR, size_limit=3 * 2**30)


# ── Key builders ─────────────────────────────────────────────

def _key(prefix: str, *parts) -> str:
    raw = f"{prefix}:" + ":".join(str(p) for p in parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# ── Audio cache ──────────────────────────────────────────────

def get_cached_audio(narration: str, voice: str, speed: str) -> str | None:
    """Returns path to a cached audio file, or None if not cached / file missing."""
    k = _key("audio", narration, voice, speed)
    cached_path = _cache.get(k)
    if cached_path and os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
        return cached_path
    return None


def set_cached_audio(narration: str, voice: str, speed: str, audio_path: str):
    """Copies audio_path into the cache store and records it (7-day TTL)."""
    if not audio_path or not os.path.exists(audio_path):
        return
    k = _key("audio", narration, voice, speed)
    dest = os.path.join(_FILES_DIR, f"audio_{k}.mp3")
    try:
        shutil.copy2(audio_path, dest)
        _cache.set(k, dest, expire=86400 * 7)
    except Exception:
        pass


# ── Video cache ──────────────────────────────────────────────

def get_cached_video(query: str) -> str | None:
    """Returns path to a cached video file, or None if not cached / file missing."""
    k = _key("video", query.strip().lower())
    cached_path = _cache.get(k)
    if cached_path and os.path.exists(cached_path) and os.path.getsize(cached_path) > 0:
        return cached_path
    return None


def set_cached_video(query: str, video_path: str):
    """Copies video_path into the cache store (24-hour TTL)."""
    if not video_path or not os.path.exists(video_path):
        return
    k = _key("video", query.strip().lower())
    ext = os.path.splitext(video_path)[1] or ".mp4"
    dest = os.path.join(_FILES_DIR, f"video_{k}{ext}")
    try:
        shutil.copy2(video_path, dest)
        _cache.set(k, dest, expire=86400)
    except Exception:
        pass


# ── Timestamps cache ─────────────────────────────────────────

def get_cached_timestamps(narration: str, voice: str) -> list | None:
    """Returns cached word timestamp list, or None."""
    k = _key("ts", narration, voice)
    return _cache.get(k)


def set_cached_timestamps(narration: str, voice: str, timestamps: list):
    """Stores word timestamps (7-day TTL)."""
    k = _key("ts", narration, voice)
    _cache.set(k, timestamps, expire=86400 * 7)


# ── Thumbnail cache ──────────────────────────────────────────

def get_cached_thumbnail(query: str) -> bytes | None:
    """Returns cached thumbnail bytes (PNG) or None."""
    k = _key("thumb", query.strip().lower())
    return _cache.get(k)


def set_cached_thumbnail(query: str, img_bytes: bytes):
    """Stores thumbnail bytes (24-hour TTL)."""
    k = _key("thumb", query.strip().lower())
    _cache.set(k, img_bytes, expire=86400)


# ── Stats & management ───────────────────────────────────────

def cache_stats() -> dict:
    """Returns cache statistics."""
    return {
        "entries": len(_cache),
        "size_mb": round(_cache.volume() / (1024 * 1024), 1),
        "location": _CACHE_DIR,
    }


def clear_cache():
    """Wipes all cache entries and cached files."""
    _cache.clear()
    for f in os.listdir(_FILES_DIR):
        try:
            os.remove(os.path.join(_FILES_DIR, f))
        except Exception:
            pass
