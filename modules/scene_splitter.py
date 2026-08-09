"""
modules/scene_splitter.py
─────────────────────────────────────────────────────────────────────────────
Scene Timestamp Splitter for Pixelab — Custom Audio Upload Mode.

Takes the full word-timestamp list (from transcribe_engine) and the target
scene count, then splits the words evenly across N scenes.

Each scene gets:
  - narration      : str   — the words spoken in that scene
  - word_timestamps: list  — [{word, start, end}] local to scene (t=0 at scene start)
  - start_sec      : float — absolute start time in the master audio
  - end_sec        : float — absolute end time in the master audio
  - search_query   : str   — filled later by ai_director.analyze_transcript()

Usage:
    from modules.scene_splitter import split_into_scenes
    scenes = split_into_scenes(word_timestamps, total_duration, scene_count=4)
─────────────────────────────────────────────────────────────────────────────
"""
import math


def split_into_scenes(
    word_timestamps: list,
    total_duration: float,
    scene_count: int,
) -> list:
    """
    Splits a flat word-timestamp list into N scenes of roughly equal word count.

    Parameters
    ----------
    word_timestamps : list
        List of {word, start, end} dicts from transcribe_engine.transcribe_audio().
    total_duration : float
        Total audio duration in seconds.
    scene_count : int
        Number of scenes to split into.

    Returns
    -------
    list of dicts:
        [{
            "narration":       str,    # words spoken in this scene
            "word_timestamps": list,   # [{word, start, end}] — times relative to scene start
            "word_timestamps_abs": list, # [{word, start, end}] — times relative to audio start
            "start_sec":       float,  # absolute start in master audio
            "end_sec":         float,  # absolute end in master audio
            "search_query":    str,    # placeholder — filled by ai_director
        }]
    """
    # ── Sanitize total_duration & scene_count ─────────────────────────
    try:
        if isinstance(total_duration, (list, tuple)):
            total_duration = total_duration[0]
        total_duration = float(total_duration)
    except Exception:
        total_duration = 10.0

    if total_duration <= 0:
        total_duration = 10.0

    if isinstance(scene_count, (list, tuple)):
        scene_count = scene_count[0]

    if isinstance(scene_count, str):
        if scene_count.upper() == "AUTO" or not scene_count.isdigit():
            scene_count = max(2, math.ceil(total_duration / 3.5))
        else:
            scene_count = int(scene_count)
    elif not isinstance(scene_count, (int, float)) or scene_count < 1:
        scene_count = 4

    scene_count = max(1, int(scene_count))

    if not word_timestamps:
        # No timestamps — create empty placeholder scenes
        dur_per_scene = total_duration / scene_count
        return [
            {
                "narration":          "",
                "word_timestamps":    [],
                "word_timestamps_abs": [],
                "start_sec":          round(i * dur_per_scene, 3),
                "end_sec":            round((i + 1) * dur_per_scene, 3),
                "search_query":       "",
            }
            for i in range(scene_count)
        ]

    n_words = len(word_timestamps)
    words_per_scene = math.ceil(n_words / max(scene_count, 1))

    scenes = []
    for i in range(scene_count):
        start_idx = i * words_per_scene
        end_idx   = min(start_idx + words_per_scene, n_words)

        if start_idx >= n_words:
            # Fewer words than scenes — pad with empty scene at end of audio
            last_end = word_timestamps[-1]["end"] if word_timestamps else total_duration
            scenes.append({
                "narration":          "",
                "word_timestamps":    [],
                "word_timestamps_abs": [],
                "start_sec":          round(last_end, 3),
                "end_sec":            round(total_duration, 3),
                "search_query":       "",
            })
            continue

        scene_words = word_timestamps[start_idx:end_idx]

        # Absolute start/end from the master audio timeline
        abs_start = scene_words[0]["start"]
        abs_end   = scene_words[-1]["end"]

        # Extend last scene to the full audio duration so there's no gap
        if i == scene_count - 1:
            abs_end = total_duration

        # Narration text for this scene
        narration = " ".join(w["word"] for w in scene_words)

        # Word timestamps relative to this scene's start (local t=0)
        local_ts = [
            {
                "word":  w["word"],
                "start": round(w["start"] - abs_start, 3),
                "end":   round(w["end"]   - abs_start, 3),
            }
            for w in scene_words
        ]

        scenes.append({
            "narration":          narration,
            "word_timestamps":    local_ts,       # Used by subtitle renderer (local time)
            "word_timestamps_abs": scene_words,   # Absolute times (for reference)
            "start_sec":          round(abs_start, 3),
            "end_sec":            round(abs_end, 3),
            "search_query":       "",             # Filled by ai_director.analyze_transcript()
        })

    return scenes
