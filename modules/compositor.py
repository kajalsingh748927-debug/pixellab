import os
import cv2
import time
import shutil
import imageio_ffmpeg
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, vfx
from modules.stock_fetcher import get_stock_clip
from modules.subtitle_vfx import apply_cinematic_vfx
from modules.audio_engine import mix_master_audio
from modules.auto_framing import SmartAutoFramer
from modules.word_timestamps import get_word_timestamps
from modules.cache_manager import get_cached_thumbnail
from config import OUTPUT_DIR, TEMP_DIR, DEFAULT_PRESET, DEFAULT_BITRATE


def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode('ascii', errors='ignore').decode('ascii'))
        except Exception:
            pass

# Resolution presets
RESOLUTION_MAP = {
    "3840×2160 (4K Ultra HD)":   (3840, 2160),
    "2160×3840 (4K Portrait)":   (2160, 3840),
    "1920×1080 (Full HD)":       (1920, 1080),
    "1280×720 (HD)":             (1280, 720),
    "1080×1920 (Portrait FHD)":  (1080, 1920),
    "1080×1080 (Square)":        (1080, 1080),
}


def build_master_video(scenes, config, output_filename="final_video.mp4", progress_callback=None, uploaded_audio_path=None):
    """
    Unified entry point for master video assembly.
    Calls build_master_video_from_audio directly.
    """
    audio_path = uploaded_audio_path or os.path.join(OUTPUT_DIR, "uploaded_audio.mp3")
    return build_master_video_from_audio(
        scenes=scenes,
        uploaded_audio_path=audio_path,
        config=config,
        output_filename=output_filename,
        progress_callback=progress_callback,
    )


def probe_encoder(codec: str) -> bool:
    """
    Quick sanity-check: run a 1-frame FFmpeg null encode to verify the
    requested codec is actually available on this machine.
    Returns True if the codec works, False otherwise.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    try:
        result = subprocess.run(
            [
                ffmpeg_exe, "-y",
                "-f", "lavfi", "-i", "color=c=black:s=16x16:r=1",
                "-frames:v", "1",
                "-c:v", codec,
                "-f", "null", "-",
            ],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def safe_encoder_config(encoder_choice: str):
    """
    Resolve the user's encoder preference to a (codec, ffmpeg_params) pair.
    If the preferred GPU encoder fails the probe test, auto-falls back to
    libx264 so the render never crashes due to missing CUDA/QSV drivers.
    """
    if "NVENC" in encoder_choice:
        if probe_encoder("h264_nvenc"):
            safe_print("✅ NVENC GPU encoder confirmed — using h264_nvenc")
            return "h264_nvenc", ["-preset", "p1", "-pix_fmt", "yuv420p"]
        safe_print("⚠️  NVENC not available (no CUDA driver) — falling back to libx264")
    elif "QuickSync" in encoder_choice:
        if probe_encoder("h264_qsv"):
            safe_print("✅ QuickSync GPU encoder confirmed — using h264_qsv")
            return "h264_qsv", ["-preset", "veryfast", "-pix_fmt", "nv12"]
        safe_print("⚠️  QuickSync not available — falling back to libx264")
    # Default / fallback
    safe_print("🖥️  Using CPU encoder: libx264")
    return "libx264", ["-crf", "18", "-pix_fmt", "yuv420p"]


def apply_subtitles_with_time(clip, narration, duration, config, word_timestamps=None):
    def subtitle_filter(get_frame, t):
        return apply_cinematic_vfx(
            get_frame(t), narration, t, duration, config,
            word_timestamps=word_timestamps
        )
    return clip.transform(subtitle_filter)


def concatenate_audio_files(audio_files, output_path):
    """
    Concatenates multiple MP3/WAV audio files into one seamless master audio
    file using ffmpeg directly (no gaps, no re-encoding artifacts).
    Returns the output_path on success, or None on failure.
    """
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    # Write a concat list file
    list_path = os.path.join(TEMP_DIR, "audio_concat_list.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for af in audio_files:
            abs_path = os.path.abspath(af).replace("\\", "/").replace("'", "\\'")
            f.write(f"file '{abs_path}'\n")

    cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c:a", "libmp3lame", "-q:a", "2",
        output_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return output_path
        safe_print(f"⚠️ Audio concat stderr: {result.stderr[-400:]}")
    except Exception as e:
        safe_print(f"⚠️ Audio concat error: {e}")
    return None



    if enable_trans and len(processed_clips) > 1:
        t_start_trans = time.time()
        update_and_notify(84, f"🔀 Applying cinematic transitions to {len(processed_clips)} scenes...")
        safe_print(f"🔀 Applying randomized cinematic transitions (duration: {trans_dur:.2f}s)...")
        from modules.transitions import get_random_transition, apply_transition

        loaded_clips = [VideoFileClip(c) for c in processed_clips if os.path.exists(c)]
        if loaded_clips:
            last_trans = None
            cur_clip = loaded_clips[0]
            trans_log = []
            for idx in range(1, len(loaded_clips)):
                next_clip = loaded_clips[idx]
                chosen_trans = get_random_transition(exclude=[last_trans])
                last_trans = chosen_trans
                trans_log.append(f"Scene {idx}➔{idx+1}: {chosen_trans}")
                cur_clip = apply_transition(cur_clip, next_clip, chosen_trans, duration=trans_dur)

            master_video_clip = cur_clip
            t_trans = time.time() - t_start_trans
            safe_print(f"  ✅ Transitions completed in {t_trans:.2f}s: {', '.join(trans_log)}")

    if master_video_clip is None:
        # Stream-copy fast path (when enable_transitions=False)
        update_and_notify(84, f"⚡ Joining {len(processed_clips)} scene video chunks (fast stream copy)...")
        concat_list_path = os.path.join(TEMP_DIR, "video_concat_list.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for cfile in processed_clips:
                escaped = cfile.replace("\\", "/").replace("'", "\\'")
                f.write(f"file '{escaped}'\n")

        unmuxed_video_path = os.path.join(TEMP_DIR, "unmuxed_master.mp4")
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        concat_cmd = [
            ffmpeg_exe, "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list_path,
            "-c", "copy",
            unmuxed_video_path
        ]
        subprocess.run(concat_cmd, capture_output=True, timeout=120)

        use_stream_copy = False
        if unmuxed_video_path and os.path.exists(unmuxed_video_path):
            try:
                m_clip = VideoFileClip(unmuxed_video_path)
                if abs(m_clip.duration - expected_total_duration) <= 1.0 and len(processed_clips) > 0:
                    master_video_clip = m_clip
                    use_stream_copy = True
                    safe_print(f"  ✅ FFmpeg stream concat successfully joined all {len(processed_clips)} clips ({m_clip.duration:.1f}s).")
                else:
                    safe_print(f"⚠️ FFmpeg concat joined only {m_clip.duration:.1f}s out of expected {expected_total_duration:.1f}s — joining ALL {len(processed_clips)} scene clips with MoviePy compose...")
                    m_clip.close()
            except Exception as mc_err:
                safe_print(f"⚠️ Master clip load error: {mc_err} — falling back to MoviePy compose.")

        if not use_stream_copy:
            loaded_clips = [VideoFileClip(c) for c in processed_clips if os.path.exists(c)]
            master_video_clip = concatenate_videoclips(loaded_clips, method="compose")
            safe_print(f"  ✅ MoviePy compose joined all {len(loaded_clips)} scene clips ({master_video_clip.duration:.1f}s).")

    final_audio_path_to_mux = master_audio_path

    if master_audio_clip is not None:
        try:
            final_audio = mix_master_audio(
                audio_clips_for_mixing, master_video_clip.duration, config,
                master_voiceover_path=master_audio_path, scenes=scenes
            )
            master_video_clip = master_video_clip.with_audio(final_audio)
            mixed_wav_path = os.path.join(TEMP_DIR, "mixed_5layer_master.wav")
            final_audio.write_audiofile(mixed_wav_path, fps=44100, logger="bar")
            if os.path.exists(mixed_wav_path) and os.path.getsize(mixed_wav_path) > 1000:
                final_audio_path_to_mux = mixed_wav_path
            safe_print("  ✅ 5-layer master audio track mixed & rendered.")
        except Exception as ae:
            safe_print(f"  ⚠️ 5-layer mix notice: {ae} — using voiceover track.")
            try:
                master_video_clip = master_video_clip.with_audio(master_audio_clip)
            except Exception:
                pass

    # Write the master video (with embedded audio via MoviePy)
    temp_audio_path = os.path.join(TEMP_DIR, "temp-audio.m4a")
    master_write_kwargs = dict(
        codec=codec,
        audio_codec="aac",
        fps=FPS,
        bitrate=DEFAULT_BITRATE,
        ffmpeg_params=ffmpeg_params,
        temp_audiofile=temp_audio_path,
        remove_temp=True,
        logger="bar",
    )
    if codec == "libx264":
        master_write_kwargs["preset"] = DEFAULT_PRESET

    video_no_audio_path = os.path.join(TEMP_DIR, "master_no_audio.mp4")
    master_video_clip.write_videofile(video_no_audio_path, **master_write_kwargs)

    # ── Guaranteed FFmpeg audio mux pass ──────────────────────────────────────
    # Muxes the full 5-layer audio track (or master voiceover fallback) via FFmpeg
    # so final_video.mp4 is 100% guaranteed to have synced, high-quality audio.
    audio_src = final_audio_path_to_mux if (final_audio_path_to_mux and os.path.exists(final_audio_path_to_mux)) else master_audio_path
    safe_print(f"  🎵 FFmpeg final audio mux: '{audio_src}' onto video...")
    try:
        mux_cmd = [
            ffmpeg_exe, "-y",
            "-i", video_no_audio_path,
            "-i", audio_src,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            final_output_path,
        ]
        mux_result = subprocess.run(mux_cmd, capture_output=True, timeout=300)
        if os.path.exists(final_output_path) and os.path.getsize(final_output_path) > 1000:
            safe_print("  ✅ Audio muxed successfully into final_video.mp4 via FFmpeg.")
        else:
            safe_print("  ⚠️ FFmpeg mux produced no output — using video file.")
            shutil.copy2(video_no_audio_path, final_output_path)
    except Exception as mux_err:
        safe_print(f"  ⚠️ FFmpeg mux error: {mux_err} — copying video file.")
        shutil.copy2(video_no_audio_path, final_output_path)

    total_time = time.time() - start_time
    safe_print(f"\n🎉 Done: {final_output_path}  (Total time: {fmt_time(total_time)})")

    # ── Cleanup ─────────────────────────────────────────────
    for c in processed_clips:
        try: c.close()
        except: pass
    for a in audio_clips_for_mixing:
        try: a.close()
        except: pass
    if master_audio_clip:
        try: master_audio_clip.close()
        except: pass
    try: master_video_clip.close()
    except: pass

    if os.path.exists(TEMP_DIR):
        for item in os.listdir(TEMP_DIR):
            p = os.path.join(TEMP_DIR, item)
            try:
                if os.path.isfile(p): os.remove(p)
            except: pass

    update_and_notify(
        100,
        f"🎉 Video complete! | "
        f"✅ {scenes_done}/{total_scenes} scenes rendered | "
        f"⏱️ Total time: {fmt_time(total_time)}"
    )
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Custom Audio Upload Mode — Master Compositor
# ─────────────────────────────────────────────────────────────────────────────

def build_master_video_from_audio(
    scenes: list,
    uploaded_audio_path: str,
    config: dict,
    output_filename: str = "final_video.mp4",
    progress_callback=None,
) -> bool:
    """
    Builds a complete video using the user's uploaded audio file.

    Differences from build_master_video():
      - Phase 1 (TTS generation) is SKIPPED — no TTS audio is generated.
      - Phase 2 (audio concat) is SKIPPED — uploaded audio is used directly.
      - Each scene's video duration = scene['end_sec'] - scene['start_sec'].
      - Subtitles are rendered using scene['word_timestamps'] (local t=0 times).
      - Final audio = uploaded audio (+ optional background music auto-ducked).

    Parameters
    ----------
    scenes : list
        Output of scene_splitter.split_into_scenes() with 'search_query' filled
        by ai_director.analyze_transcript().
        Each scene must have: narration, word_timestamps, start_sec, end_sec, search_query.
    uploaded_audio_path : str
        Absolute path to the user's uploaded audio file.
    config : dict
        Video config from sidebar (resolution, fps, encoder, VFX flags, etc.)
    output_filename : str
        Output file name inside OUTPUT_DIR.
    progress_callback : callable | None
        Same signature as build_master_video: (pct, msg, scene_states, elapsed).
    """
    final_output_path = os.path.join(OUTPUT_DIR, output_filename)
    processed_clips   = []
    total_scenes      = len(scenes)

    res_key      = config.get("resolution", "1920×1080 (Full HD)")
    VIDEO_W, VIDEO_H = RESOLUTION_MAP.get(res_key, (1920, 1080))
    FPS          = config.get("fps", 24)
    fade_dur     = config.get("fade_duration", 0) if config.get("enable_fade") else 0

    # Determine Hardware Accelerated Encoder
    encoder_choice = config.get("encoder", "CPU (libx264 — Universal)")
    codec, ffmpeg_params = safe_encoder_config(encoder_choice)

    start_time = time.time()

    def fmt_time(seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s:02d}s"

    # Build scene state tracking objects (same structure as build_master_video)
    scene_states = [
        {
            "index":            i + 1,
            "narration":        sc.get("narration", ""),
            "english_subtitle": sc.get("english_subtitle", sc.get("narration", "")),
            "emphasis_words":   sc.get("emphasis_words", []),
            "map_location":     sc.get("map_location"),
            "fact_card":        sc.get("fact_card"),
            "query":            sc.get("search_query", ""),
            "audio_status":     "✅ Uploaded Audio",   # Audio is pre-provided
            "video_status":     "⏳ Pending",
            "vfx_status":       "⏳ Pending",
            "overall":          "⏳ Pending",
            "thumbnail":        None,
            "word_ts":          sc.get("word_timestamps", []),
        }
        for i, sc in enumerate(scenes)
    ]

    def update_and_notify(pct, msg):
        elapsed = time.time() - start_time
        if progress_callback:
            progress_callback(pct, msg, scene_states, elapsed)

    update_and_notify(5, f"🎤 Custom Audio Mode — Building {total_scenes} scenes from uploaded audio...")

    # Build dummy per-scene AudioFileClip stubs (needed for SFX boundary timing in mix_master_audio)
    # We create silent clips of the correct duration to represent each scene's time window
    audio_clips_for_mixing = []

    scenes_done   = 0
    scenes_failed = 0

    # ── PHASE: Build video clips per scene ────────────────────────────────────
    # ⚡ High-Speed Optimization: Pre-download all stock clips concurrently in parallel threads
    update_and_notify(8, f"⚡ Parallel stock downloader fetching {total_scenes} scene clips concurrently...")
    from modules.stock_fetcher import fetch_stock_clips_parallel
    pre_fetched_clips = fetch_stock_clips_parallel(scenes)

    for idx, sc in enumerate(scenes, start=1):
        cur_state = scene_states[idx - 1]


        narration  = sc.get("narration", "")
        query      = sc.get("search_query", "nature")
        start_sec  = sc.get("start_sec", 0.0)
        end_sec    = sc.get("end_sec", 10.0)
        audio_dur  = max(end_sec - start_sec, 1.0)   # Duration for this scene's video clip
        word_ts    = sc.get("word_timestamps", [])   # Already local (t=0 at scene start)

        scenes_left   = total_scenes - idx
        elapsed       = time.time() - start_time
        avg_per_scene = elapsed / max(idx - 1, 1)
        eta_sec       = avg_per_scene * scenes_left
        eta_str       = fmt_time(eta_sec) if idx > 1 else "Calculating..."

        base_pct = int(10 + ((idx - 1) / max(total_scenes, 1)) * 72)
        update_and_notify(
            base_pct,
            f"🎬 Scene {idx}/{total_scenes} | "
            f"⏱️ {start_sec:.1f}s–{end_sec:.1f}s | "
            f"✅ {scenes_done} Done | ⏳ {scenes_left} Left | ETA: {eta_str}"
        )

        safe_print(f"\n🎬 Scene {idx}/{total_scenes}: '{query}' | {start_sec:.1f}s–{end_sec:.1f}s ({audio_dur:.1f}s)")
        cur_state["overall"] = "🔄 In Progress"

        # ── Stock footage ──────────────────────────────────────────────────────
        cur_state["video_status"] = "🔍 Searching stock libraries..."

        def stock_cb(stage, s_idx, q, _idx=idx, _cur=cur_state):
            if stage == "downloading_video":
                _cur["video_status"] = f"⏬ Downloading ({q.split('(')[-1].strip(')')})..."
                update_and_notify(base_pct + 3, f"⏬ Scene {_idx}: Downloading '{q}'...")
            elif stage == "video_downloaded":
                _cur["video_status"] = "✅ Video Downloaded"

        video_file = get_stock_clip(query, idx, progress_callback=stock_cb)

        if not video_file or not os.path.exists(video_file):
            safe_print(f"⚠️ No video for scene {idx}, skipping.")
            cur_state["video_status"] = "❌ Download Failed"
            cur_state["overall"]      = "❌ Failed"
            scenes_failed += 1
            continue

        cur_state["video_status"] = "✅ Video Ready"
        cur_state["vfx_status"]   = "🎨 Applying VFX..."

        # Retrieve cached thumbnail
        thumb_bytes = get_cached_thumbnail(query)
        if thumb_bytes:
            cur_state["thumbnail"] = thumb_bytes

        # ── Crop & Resize (AI Auto-Framing) ────────────────────────────────────
        clip = VideoFileClip(video_file)
        w, h = clip.size
        target_ratio  = VIDEO_W / VIDEO_H
        current_ratio = w / h

        enable_auto_frame = config.get("enable_auto_framing", True)
        is_portrait_crop  = (VIDEO_W < VIDEO_H)

        if enable_auto_frame and is_portrait_crop and current_ratio > target_ratio:
            framer = SmartAutoFramer(w, h, VIDEO_W, VIDEO_H, smoothing=0.06)
            def auto_frame_filter(get_frame, t, _framer=framer):
                return _framer.crop_frame(get_frame(t))
            clip = clip.transform(auto_frame_filter)
            safe_print(f"  🎯 AI Auto-Framing active ({w}x{h} → {VIDEO_W}x{VIDEO_H})")
        else:
            if current_ratio > target_ratio:
                new_w = int(h * target_ratio)
                clip  = clip.cropped(x1=(w - new_w) // 2, width=new_w)
            elif current_ratio < target_ratio:
                new_h = int(w / target_ratio)
                clip  = clip.cropped(y1=(h - new_h) // 2, height=new_h)
            clip = clip.resized(new_size=(VIDEO_W, VIDEO_H))

        # ── Loop/trim video to match this scene's audio duration ────────────────
        if clip.duration < audio_dur:
            clip = clip.with_effects([vfx.Loop(duration=audio_dur)])
        else:
            clip = clip.subclipped(0, audio_dur)

        # ── Ken Burns zoom ──────────────────────────────────────────────────────
        if config.get("enable_zoom"):
            direction = config.get("zoom_direction", "Slow Zoom In")
            def zoom_filter(get_frame, t, dur=audio_dur, d=direction):
                frame = get_frame(t)
                progress = t / max(dur, 0.1)
                if d == "Slow Zoom In":
                    scale = 1.0 + 0.04 * progress
                elif d == "Slow Zoom Out":
                    scale = 1.04 - 0.04 * progress
                else:
                    import random
                    scale = 1.0 + 0.04 * (progress if random.random() > 0.5 else (1 - progress))
                fh, fw = frame.shape[:2]
                nw2, nh2 = int(fw * scale), int(fh * scale)
                resized = cv2.resize(frame, (nw2, nh2))
                x1, y1 = (nw2 - fw) // 2, (nh2 - fh) // 2
                return resized[y1:y1+fh, x1:x1+fw]
            clip = clip.transform(zoom_filter)

        # ── Kinetic Subtitles + VFX (word timestamps are already local t=0) ────
        sub_text_to_render = cur_state.get("english_subtitle") or narration
        ts_for_sub = word_ts if (sub_text_to_render == narration) else None

        scene_cfg = dict(config)
        scene_cfg["emphasis_words"] = cur_state.get("emphasis_words", [])
        scene_cfg["fact_card"]      = cur_state.get("fact_card")
        scene_cfg["map_location"]   = cur_state.get("map_location")

        def subtitle_filter(get_frame, t, _text=sub_text_to_render, _ts=ts_for_sub, _cfg=scene_cfg):

            return apply_cinematic_vfx(
                get_frame(t), _text, t, audio_dur, _cfg,
                word_timestamps=_ts,
            )
        clip = clip.transform(subtitle_filter)



        # ── Crossfade transition ────────────────────────────────────────────────
        if fade_dur > 0:
            clip = clip.with_effects([vfx.CrossFadeIn(fade_dur), vfx.CrossFadeOut(fade_dur)])

        # ── Write scene chunk ───────────────────────────────────────────────────
        chunk_file      = os.path.join(TEMP_DIR, f"scene_chunk_{idx:02d}.mp4")
        temp_audio_path = os.path.join(TEMP_DIR, f"temp_chunk_audio_{idx:02d}.m4a")

        write_kwargs = dict(
            codec=codec,
            audio=False,            # No per-scene audio — uploaded audio is muxed at the end
            fps=FPS,
            bitrate=DEFAULT_BITRATE,
            ffmpeg_params=ffmpeg_params,
            logger="bar",
        )
        if codec == "libx264":
            write_kwargs["preset"] = DEFAULT_PRESET

        clip.write_videofile(chunk_file, **write_kwargs)
        clip.close()
        del clip
        import gc; gc.collect()
        processed_clips.append(chunk_file)

        # Create a silent placeholder clip of correct duration for SFX boundary timing
        try:
            # We need a dummy clip duration — create a tiny silence stub
            silence_path = os.path.join(TEMP_DIR, f"silence_{idx:02d}.mp3")
            silence_cmd = [
                imageio_ffmpeg.get_ffmpeg_exe(), "-y",
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
                "-t", str(audio_dur), "-q:a", "9", "-acodec", "libmp3lame", silence_path
            ]
            subprocess.run(silence_cmd, capture_output=True, timeout=15)
            if os.path.exists(silence_path):
                audio_clips_for_mixing.append(AudioFileClip(silence_path))
        except Exception:
            pass

        cur_state["vfx_status"] = "✅ Complete"
        cur_state["overall"]    = "✅ Complete"
        scenes_done += 1

        elapsed     = time.time() - start_time
        scenes_left = total_scenes - idx
        avg_per_scene = elapsed / max(scenes_done, 1)
        eta_sec     = avg_per_scene * scenes_left
        update_and_notify(
            int(10 + (idx / max(total_scenes, 1)) * 72),
            f"✅ Scene {idx}/{total_scenes} complete! | "
            f"✅ {scenes_done} Done | ⏳ {scenes_left} Left | "
            f"⏱️ {fmt_time(elapsed)} elapsed | ETA: {fmt_time(eta_sec)}"
        )

    # ── Final render ───────────────────────────────────────────────────────────
    if not processed_clips:
        safe_print("❌ No clips processed.")
        update_and_notify(0, "❌ No clips were successfully processed.")
        return False

    # ── Master Video Assembly (Transitions vs Fast Stream Copy) ──────
    enable_trans = config.get("enable_transitions", True)
    trans_dur    = config.get("transition_duration", 0.35)
    expected_total_duration = sum(sc.get("end_sec", 10.0) - sc.get("start_sec", 0.0) for sc in scenes)

    master_video_clip = None

    if enable_trans and len(processed_clips) > 1:
        t_start_trans = time.time()
        update_and_notify(84, f"🔀 Applying cinematic transitions to {len(processed_clips)} scenes...")
        safe_print(f"🔀 Applying randomized cinematic transitions (duration: {trans_dur:.2f}s)...")
        from modules.transitions import get_random_transition, apply_transition

        loaded_clips = [VideoFileClip(c) for c in processed_clips if os.path.exists(c)]
        if loaded_clips:
            last_trans = None
            cur_clip = loaded_clips[0]
            trans_log = []
            for idx in range(1, len(loaded_clips)):
                next_clip = loaded_clips[idx]
                chosen_trans = get_random_transition(exclude=[last_trans])
                last_trans = chosen_trans
                trans_log.append(f"Scene {idx}➔{idx+1}: {chosen_trans}")
                cur_clip = apply_transition(cur_clip, next_clip, chosen_trans, duration=trans_dur)

            master_video_clip = cur_clip
            t_trans = time.time() - t_start_trans
            safe_print(f"  ✅ Transitions completed in {t_trans:.2f}s: {', '.join(trans_log)}")

    if master_video_clip is None:
        # Stream-copy fast path (when enable_transitions=False)
        update_and_notify(84, f"⚡ Joining {len(processed_clips)} scene video chunks (fast stream copy)...")
        concat_list_path = os.path.join(TEMP_DIR, "video_concat_list.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for cfile in processed_clips:
                escaped = cfile.replace("\\", "/").replace("'", "\\'")
                f.write(f"file '{escaped}'\n")

        unmuxed_video_path = os.path.join(TEMP_DIR, "unmuxed_master.mp4")
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        concat_cmd = [
            ffmpeg_exe, "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list_path,
            "-c", "copy",
            unmuxed_video_path
        ]
        subprocess.run(concat_cmd, capture_output=True, timeout=120)

        use_stream_copy = False
        if unmuxed_video_path and os.path.exists(unmuxed_video_path):
            try:
                m_clip = VideoFileClip(unmuxed_video_path)
                if abs(m_clip.duration - expected_total_duration) <= 1.0 and len(processed_clips) > 0:
                    master_video_clip = m_clip
                    use_stream_copy = True
                    safe_print(f"  ✅ FFmpeg stream concat successfully joined all {len(processed_clips)} clips ({m_clip.duration:.1f}s).")
                else:
                    safe_print(f"⚠️ FFmpeg concat joined only {m_clip.duration:.1f}s out of expected {expected_total_duration:.1f}s — joining ALL {len(processed_clips)} scene clips with MoviePy compose...")
                    m_clip.close()
            except Exception as mc_err:
                safe_print(f"⚠️ Master clip load error: {mc_err} — falling back to MoviePy compose.")

        if not use_stream_copy:
            loaded_clips = [VideoFileClip(c) for c in processed_clips if os.path.exists(c)]
            master_video_clip = concatenate_videoclips(loaded_clips, method="compose")
            safe_print(f"  ✅ MoviePy compose joined all {len(loaded_clips)} scene clips ({master_video_clip.duration:.1f}s).")

    # ── Mux uploaded audio + optional background music ─────────────────────────
    update_and_notify(88, "🎤 Muxing uploaded audio + background music into final video...")
    try:
        final_audio = mix_master_audio(
            audio_clips_for_mixing,
            master_video_clip.duration,
            config,
            uploaded_audio_path=uploaded_audio_path,
            scenes=scenes,
        )
        master_video_clip = master_video_clip.with_audio(final_audio)
        safe_print("  ✅ Uploaded audio + music track multiplexed.")
    except Exception as ae:
        safe_print(f"  ⚠️ Audio mix notice: {ae} — trying direct audio mux...")
        # Direct FFmpeg fallback — mux uploaded audio directly without music
        try:
            direct_out = final_output_path.replace(".mp4", "_direct.mp4")
            mux_cmd = [
                ffmpeg_exe, "-y",
                "-i", unmuxed_video_path if os.path.exists(unmuxed_video_path) else processed_clips[0],
                "-i", uploaded_audio_path,
                "-c:v", "copy", "-c:a", "aac",
                "-shortest", direct_out,
            ]
            result = subprocess.run(mux_cmd, capture_output=True, timeout=180)
            if os.path.exists(direct_out):
                shutil.move(direct_out, final_output_path)
                total_time = time.time() - start_time
                safe_print(f"\n🎉 Done (direct mux fallback): {final_output_path} ({fmt_time(total_time)})")
                update_and_notify(
                    100,
                    f"🎉 Video complete! | ✅ {scenes_done}/{total_scenes} scenes | ⏱️ {fmt_time(total_time)}"
                )
                return True
        except Exception as direct_err:
            safe_print(f"  ❌ Direct mux also failed: {direct_err}")

    # ── Final write ────────────────────────────────────────────────────────────
    temp_audio_path = os.path.join(TEMP_DIR, "temp-audio.m4a")
    master_write_kwargs = dict(
        codec=codec,
        audio_codec="aac",
        fps=FPS,
        bitrate=DEFAULT_BITRATE,
        ffmpeg_params=ffmpeg_params,
        temp_audiofile=temp_audio_path,
        remove_temp=True,
        logger="bar",
    )
    if codec == "libx264":
        master_write_kwargs["preset"] = DEFAULT_PRESET

    master_video_clip.write_videofile(final_output_path, **master_write_kwargs)

    total_time = time.time() - start_time
    safe_print(f"\n🎉 Done: {final_output_path}  (Total time: {fmt_time(total_time)})")

    # ── Cleanup ────────────────────────────────────────────────────────────────
    for a in audio_clips_for_mixing:
        try: a.close()
        except: pass
    try: master_video_clip.close()
    except: pass

    if os.path.exists(TEMP_DIR):
        for item in os.listdir(TEMP_DIR):
            p = os.path.join(TEMP_DIR, item)
            try:
                if os.path.isfile(p): os.remove(p)
            except: pass

    update_and_notify(
        100,
        f"🎉 Video complete! | "
        f"✅ {scenes_done}/{total_scenes} scenes rendered | "
        f"⏱️ Total time: {fmt_time(total_time)}"
    )
    return True