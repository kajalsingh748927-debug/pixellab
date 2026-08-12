"""
modules/session_persistence.py
─────────────────────────────────────────────────────────────────────────────
Automatic Local Disk Session & Project Checkpoint Engine for Pixelab.

Saves user session state (uploaded audio, generated script, settings, progress)
to output/temp/project_checkpoint.json so page refreshes and server restarts
never lose data or progress.
─────────────────────────────────────────────────────────────────────────────
"""
import os
import json
import logging

logger = logging.getLogger("pixelab.session_persistence")

CHECKPOINT_FILE = os.path.join("output", "temp", "project_checkpoint.json")


def save_project_checkpoint(video_config: dict, scenes: list = None, script_text: str = None, audio_path: str = None) -> bool:
    """Saves current user session state to disk."""
    try:
        os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)

        # Sanitize config dict for JSON serializability
        clean_config = {}
        if isinstance(video_config, dict):
            for k, v in video_config.items():
                if isinstance(v, (str, int, float, bool, list, dict, type(None))):
                    clean_config[k] = v
                elif isinstance(v, tuple):
                    clean_config[k] = list(v)

        data = {
            "video_config": clean_config,
            "scenes": scenes or [],
            "script_text": script_text or "",
            "audio_path": audio_path or "",
        }

        with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("[CHECKPOINT] Session saved successfully.")
        return True
    except Exception as e:
        logger.error(f"[CHECKPOINT] Save failed: {e}")
        return False


def load_project_checkpoint() -> dict:
    """Loads session checkpoint from disk if available."""
    if not os.path.exists(CHECKPOINT_FILE):
        return {}

    try:
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Re-convert tuple fields in video_config if needed
        cfg = data.get("video_config", {})
        for k in ["outro_gradient_colors"]:
            if k in cfg and isinstance(cfg[k], list):
                cfg[k] = tuple(tuple(c) if isinstance(c, list) else c for c in cfg[k])

        logger.info("[CHECKPOINT] Session loaded from checkpoint file.")
        return data
    except Exception as e:
        logger.error(f"[CHECKPOINT] Load error: {e}")
        return {}


def clear_project_checkpoint() -> bool:
    """Clears checkpoint file for fresh projects."""
    try:
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
            logger.info("[CHECKPOINT] Checkpoint cleared.")
        return True
    except Exception as e:
        logger.error(f"[CHECKPOINT] Clear error: {e}")
        return False
