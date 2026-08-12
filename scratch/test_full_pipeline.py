"""
scratch/test_full_pipeline.py
Directly tests build_master_video_from_audio on output/uploaded_audio.mp3 using output/temp/project_checkpoint.json.
Prints real-time progress and captures any tracebacks.
"""
import os
import sys
import time
import json
import traceback

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TEMP_DIR, OUTPUT_DIR
from modules.compositor import build_master_video_from_audio

def progress_cb(pct, status, *args):
    try:
        print(f"[{pct:3d}%] {status}")
    except Exception:
        print(f"[{pct:3d}%] {str(status).encode('ascii', errors='ignore').decode('ascii')}")

def main():
    audio_path = os.path.join(OUTPUT_DIR, "uploaded_audio.mp3")
    final_output_path = os.path.join(OUTPUT_DIR, "final_video.mp4")
    checkpoint_path = os.path.join(TEMP_DIR, "project_checkpoint.json")

    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        sys.exit(1)

    scenes = []
    config = {
        "resolution": "1920×1080 (Full HD)",
        "fps": 24,
        "fade_duration": 0,
        "enable_fade": False,
        "encoder": "CPU (libx264 — Universal)",
        "show_intro": True,
        "show_outro": True,
        "show_chapter_cards": True,
        "enable_transitions": True,
    }

    if os.path.exists(checkpoint_path):
        print(f"Loading checkpoint from {checkpoint_path}...")
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            scenes = data.get("scenes", [])
            saved_cfg = data.get("config", {})
            config.update(saved_cfg)

    print(f"Starting direct test on uploaded audio: {audio_path}")
    print(f"Total scenes to process: {len(scenes)}")
    print(f"Output path: {final_output_path}")

    start_t = time.time()
    try:
        success = build_master_video_from_audio(
            scenes=scenes,
            uploaded_audio_path=audio_path,
            config=config,
            output_filename="final_video.mp4",
            progress_callback=progress_cb,
        )
        dur = time.time() - start_t
        if success and os.path.exists(final_output_path):
            size_mb = os.path.getsize(final_output_path) / (1024 * 1024)
            print(f"\nSUCCESS! Rendered final video: {final_output_path}")
            print(f"File size: {size_mb:.2f} MB | Total execution time: {dur:.2f}s")
        else:
            print(f"\nFAILED: Render function returned {success}")
    except Exception as e:
        print(f"\nEXCEPTION DETECTED: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
