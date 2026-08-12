"""
modules/error_handler.py
─────────────────────────────────────────────────────────────────────────────
Comprehensive Error & Exception Handling System for Pixelab.

Provides:
  • Custom Exception Hierarchy (PixelabBaseError, APIKeyError, TranscribeError, FFmpegRenderError, StockFetchError, FileIOError)
  • Specific Exception Types & Global Exception Handler
  • User-Friendly Error Formatting & Detailed Stacktrace Logging
  • Timeout & Exponential Backoff Retry Handling
  • Graceful Shutdown & Resource Cleanup (try/except/else/finally)
─────────────────────────────────────────────────────────────────────────────
"""
import sys
import os
import time
import logging
import traceback
from functools import wraps

# Setup structured logger
logger = logging.getLogger("pixelab_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s', datefmt='%H:%M:%S')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


# ── 1. CUSTOM EXCEPTION HIERARCHY ───────────────────────────────────────────
class PixelabBaseError(Exception):
    """Base exception for all Pixelab runtime errors."""
    def __init__(self, message: str, user_friendly_msg: str = None):
        super().__init__(message)
        self.message = message
        self.user_friendly_msg = user_friendly_msg or message

class APIKeyError(PixelabBaseError):
    """Raised when an API key (Groq, Pexels, ElevenLabs) is missing or invalid."""
    pass

class TranscribeError(PixelabBaseError):
    """Raised when Whisper or ElevenLabs audio transcription fails."""
    pass

class StockFetchError(PixelabBaseError):
    """Raised when Pexels API fails to fetch HD video assets."""
    pass

class FFmpegRenderError(PixelabBaseError):
    """Raised when OpenCV or FFmpeg fails during video synthesis."""
    pass

class FileIOError(PixelabBaseError):
    """Raised when audio/video files cannot be read or written."""
    pass


# ── 2. RETRY DECORATOR WITH EXPONENTIAL BACKOFF & TIMEOUT HANDLING ─────────
def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 1.5, allowed_exceptions=(Exception,)):
    """
    Decorator for robust API & File operations with automatic retries and exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = 1.0
            last_err = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    last_err = e
                    logger.warning(f"⚠️ [{func.__name__}] Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    delay *= backoff_factor
                else:
                    break
            logger.error(f"❌ [{func.__name__}] All {max_retries} retries failed.")
            raise last_err
        return wrapper
    return decorator


# ── 3. GLOBAL EXCEPTION HANDLER & USER-FRIENDLY ERROR MESSAGING ──────────────
def handle_exception(e: Exception, context_name: str = "Operation") -> dict:
    """
    Global exception handler that logs full stacktraces silently to stderr
    and formats user-friendly error messages for UI rendering.
    """
    tb_str = traceback.format_exc()
    logger.error(f"[ERROR] Exception in {context_name}:\n{tb_str}")

    user_msg = getattr(e, "user_friendly_msg", None)
    if not user_msg:
        if isinstance(e, APIKeyError):
            user_msg = "🔑 API Key Missing or Invalid — Please verify your keys in the sidebar."
        elif isinstance(e, TranscribeError):
            user_msg = "🎙️ Audio Transcription Failed — Please check your audio file format."
        elif isinstance(e, StockFetchError):
            user_msg = "📹 Stock Video Fetch Failed — Check internet connection or Pexels API key."
        elif isinstance(e, FFmpegRenderError):
            user_msg = "🎬 Video Render Failed — FFmpeg or MoviePy encoding error encountered."
        elif isinstance(e, FileIOError):
            user_msg = "📁 File Access Error — Unable to read or write persistent temp files."
        elif isinstance(e, TimeoutError):
            user_msg = "⏱️ Request Timed Out — Operation took too long to complete."
        else:
            user_msg = f"⚠️ {context_name} Error: {str(e)}"

    return {
        "success": False,
        "error_type": type(e).__name__,
        "user_message": user_msg,
        "traceback": tb_str,
    }


# ── 4. GRACEFUL SHUTDOWN & CLEANUP (try / except / else / finally) ─────────
def safe_file_cleanup(file_paths: list):
    """
    Safely cleans up temporary files using complete try / except / else / finally control flow.
    """
    cleaned_count = 0
    errors_encountered = []
    try:
        for p in file_paths:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                    cleaned_count += 1
                except Exception as fe:
                    errors_encountered.append((p, str(fe)))
    except Exception as general_err:
        logger.error(f"Error during cleanup scan: {general_err}")
    else:
        logger.info(f"[CLEANUP] Cleaned up {cleaned_count} temp files successfully.")
    finally:
        if errors_encountered:
            logger.warning(f"[WARNING] Cleanup notices: {errors_encountered}")


# ── 5. INPUT SANITIZATION & SECURITY PROTECTION ────────────────────────────
import re

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes uploaded filenames to prevent directory traversal and path manipulation attacks.
    """
    if not filename:
        return "uploaded_audio.mp3"
    # Take basename only to prevent ../ or subfolder paths
    clean_name = os.path.basename(filename)
    # Remove dangerous characters, allow only alphanumeric, underscores, hyphens, and dots
    clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', clean_name)
    return clean_name or "uploaded_audio.mp3"


def validate_uploaded_file(uploaded_file, max_size_mb: float = 200.0) -> tuple:
    """
    Validates uploaded audio file format, zero-byte status, and file size cap.
    Returns (is_valid: bool, error_message: str).
    """
    if uploaded_file is None:
        return False, "📁 No file uploaded."

    # Size check
    file_size_mb = getattr(uploaded_file, "size", 0) / (1024 * 1024)
    if file_size_mb == 0:
        return False, "⚠️ Uploaded file is empty (0 bytes)."
    if file_size_mb > max_size_mb:
        return False, f"⚠️ File size ({file_size_mb:.1f} MB) exceeds maximum allowed limit ({max_size_mb} MB)."

    # Extension check
    allowed_exts = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}
    ext = os.path.splitext(uploaded_file.name)[-1].lower()
    if ext not in allowed_exts:
        return False, f"⚠️ Format '{ext}' is not supported. Supported audio formats: MP3, WAV, M4A, OGG, FLAC, AAC."

    return True, ""


def mask_api_key(key: str) -> str:
    """
    Masks API keys for safe logging and UI display (e.g. gsk_12345678 -> gsk_••••5678).
    """
    if not key:
        return "Not Set"
    if len(key) <= 8:
        return "••••••••"
    return f"{key[:4]}••••{key[-4:]}"


def auto_purge_temp_dir(temp_dir: str, max_mb: float = 500.0):
    """
    Monitors temporary video storage quota and automatically purges oldest temp files
    when total size exceeds max_mb limit.
    """
    if not os.path.exists(temp_dir):
        return

    try:
        files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))]
        total_bytes = sum(os.path.getsize(f) for f in files)
        max_bytes = max_mb * 1024 * 1024

        if total_bytes > max_bytes:
            logger.info(f"[DISK CLEANUP] Temp disk usage ({total_bytes / 1024 / 1024:.1f} MB) exceeds quota ({max_mb} MB). Purging oldest clips...")
            # Sort files by modification time (oldest first)
            files.sort(key=lambda f: os.path.getmtime(f))
            for f in files:
                try:
                    os.remove(f)
                    total_bytes -= os.path.getsize(f)
                    if total_bytes <= max_bytes * 0.5:
                        break
                except Exception as e:
                    logger.warning(f"Could not purge {f}: {e}")
    except Exception as e:
        logger.error(f"Error during auto_purge_temp_dir: {e}")
