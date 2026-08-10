import os
import cv2
import time
import shutil
import gc
import imageio_ffmpeg
import subprocess
from moviepy import VideoFileClip, concatenate_videoclips, vfx
from modules.stock_fetcher import get_stock_clip, create_procedural_background
from modules.subtitle_vfx import apply_cinematic_vfx
from modules.auto_framing import SmartAutoFramer
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
        safe_print("⚠️ NVENC not available (no CUDA driver) — falling back to libx264")
    elif "QuickSync" in encoder_choice:
        if probe_encoder("h264_qsv"):
            safe_print("✅ QuickSync GPU encoder confirmed — using h264_qsv")
            return "h264_qsv", ["-preset", "veryfast", "-pix_fmt", "nv12"]
        safe_print("⚠️ QuickSync not available — falling back to libx264")
    # Default / fallback
    safe_print("🖥️ Using CPU encoder: libx264")
    return "libx264", ["-crf", "18", "-pix_fmt", "yuv420p"]


def apply_subtitles_with_time(clip, narration, duration, config, word_timestamps=None):
    def subtitle_filter(get_frame, t):
        return apply_cinematic_vfx(
            get_frame(t), narration, t, duration, config,
            word_timestamps=word_timestamps
        )
    return clip.transform(subtitle_filter)


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
    Video-only rendering engine with direct FFmpeg audio multiplexing.
    """
    final_output_path = os.path.join(OUTPUT_DIR, output_filename)
    processed_clips   = []
    total_scenes      = len(scenes)

    res_key          = config.get("resolution", "1920×1080 (Full HD)")
    VIDEO_W, VIDEO_H = RESOLUTION_MAP.get(res_key, (1920, 1080))
    FPS              = config.get("fps", 24)
    fade_dur         = config.get("fade_duration", 0) if config.get("enable_fade") else 0

    encoder_choice       = config.get("encoder", "CPU (libx264 — Universal)")
    codec, ffmpeg_params = safe_encoder_config(encoder_choice)

    start_time = time.time()

    def fmt_time(seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s:02d}s"

    scene_states = [
        {
            "index":            i + 1,
            "narration":        sc.get("narration", ""),
            "english_subtitle": sc.get("english_subtitle", sc.get("narration", "")),
            "emphasis_words":   sc.get("emphasis_words", []),
            "map_location":     sc.get("map_location"),
            "fact_card":        sc.get("fact_card"),
            "query":            sc.get("search_query", ""),
            "audio_status":     "✅ Uploaded Audio",
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

    scenes_done   = 0

    # Pre-download all stock clips concurrently
    update_and_notify(8, f"⚡ Parallel stock downloader fetching {total_scenes} scene clips concurrently...")
    from modules.stock_fetcher import fetch_stock_clips_parallel
    pre_fetched_clips = fetch_stock_clips_parallel(scenes, api_key=config.get("groq_key"))

    for idx, sc in enumerate(scenes, start=1):
        cur_state = scene_states[idx - 1]

        narration  = sc.get("narration", "")
        query      = sc.get("search_query", "nature")
        start_sec  = sc.get("start_sec", 0.0)
        end_sec    = sc.get("end_sec", 10.0)
        audio_dur  = max(end_sec - start_sec, 1.0)
        word_ts    = sc.get("word_timestamps", [])

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
        cur_state["video_status"] = "🔍 Fetching stock clip..."

        # Use pre-fetched clip or fallback
        video_file = pre_fetched_clips[idx - 1] if (idx - 1 < len(pre_fetched_clips)) else None

        if not video_file or not os.path.exists(video_file) or os.path.getsize(video_file) < 5000:
            safe_print(f"⚠️ Clip missing or corrupt for scene {idx} — generating procedural background.")
            fallback_fn = os.path.join(TEMP_DIR, f"clip_{idx:02d}.mp4")
            create_procedural_background(fallback_fn, duration=audio_dur)
            video_file = fallback_fn

        cur_state["video_status"] = "✅ Video Ready"
        cur_state["vfx_status"]   = "🎨 Applying VFX..."

        thumb_bytes = get_cached_thumbnail(query)
        if thumb_bytes:
            cur_state["thumbnail"] = thumb_bytes

        # ── Crop & Resize (AI Auto-Framing) ────────────────────────────────────
        try:
            clip = VideoFileClip(video_file)
        except Exception as ve:
            safe_print(f"⚠️ MoviePy load error for '{video_file}': {ve} — re-generating procedural video.")
            fallback_fn = os.path.join(TEMP_DIR, f"clip_fallback_{idx:02d}.mp4")
            create_procedural_background(fallback_fn, duration=audio_dur)
            clip = VideoFileClip(fallback_fn)

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
        else:
            if current_ratio > target_ratio:
                new_w = int(h * target_ratio)
                clip  = clip.cropped(x1=(w - new_w) // 2, width=new_w)
            elif current_ratio < target_ratio:
                new_h = int(w / target_ratio)
                clip  = clip.cropped(y1=(h - new_h) // 2, height=new_h)
            clip = clip.resized(new_size=(VIDEO_W, VIDEO_H))

        # ── Loop/trim video to match scene duration ───────────────────────────
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

        # ── Kinetic Subtitles + VFX ─────────────────────────────────────────────
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

        # ── Intro Title Overlay (On Scene 1) ──────────────────────────────────
        if idx == 1 and config.get("show_intro", True):
            from modules.title_overlay import apply_intro_overlay
            intro_meta = sc.get("intro", {})
            def intro_filter(get_frame, t, _idata=intro_meta, _cfg=config):
                return apply_intro_overlay(get_frame(t), t, _idata, _cfg)
            clip = clip.transform(intro_filter)

        # ── Chapter Title Overlay (First 2.5s) ────────────────────────────────
        if sc.get("show_chapter") and config.get("show_chapter_cards", True):
            chapter = sc.get("chapter_title", f"PART {idx}")
            from modules.title_overlay import apply_chapter_overlay
            def chapter_filter(get_frame, t, _ch=chapter, _cfg=config):
                return apply_chapter_overlay(get_frame(t), t, _ch, _cfg)
            clip = clip.transform(chapter_filter)

        # ── Kinetic Info Graphic / Data Callout Overlay ────────────────────────
        if sc.get("fact_card"):
            from modules.title_overlay import apply_fact_callout_overlay
            fc_data = sc["fact_card"]
            def fact_filter(get_frame, t, _fc=fc_data, _cfg=config):
                return apply_fact_callout_overlay(get_frame(t), t, _fc, _cfg)
            clip = clip.transform(fact_filter)

        # ── Outro CTA Overlay (On Last Scene) ─────────────────────────────────
        if idx == total_scenes and config.get("show_outro", True):
            from modules.title_overlay import apply_outro_overlay
            outro_meta = sc.get("outro", {})
            def outro_filter(get_frame, t, _dur=audio_dur, _odata=outro_meta, _cfg=config):
                return apply_outro_overlay(get_frame(t), t, _dur, _odata, _cfg)
            clip = clip.transform(outro_filter)

        # ── Crossfade transition ────────────────────────────────────────────────
        if fade_dur > 0:
            clip = clip.with_effects([vfx.CrossFadeIn(fade_dur), vfx.CrossFadeOut(fade_dur)])

        # ── Write scene chunk ───────────────────────────────────────────────────
        chunk_file = os.path.join(TEMP_DIR, f"scene_chunk_{idx:02d}.mp4")

        write_kwargs = dict(
            codec=codec,
            audio=False,
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
        gc.collect()
        processed_clips.append(chunk_file)

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

    # ── Master Video Assembly (Transitions vs Fast Stream Copy) ────────────────
    enable_trans = config.get("enable_transitions", True)
    trans_dur    = config.get("transition_duration", 0.35)

    unmuxed_video_path = os.path.join(TEMP_DIR, "unmuxed_master.mp4")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    if enable_trans and len(processed_clips) > 1:
        t_start_trans = time.time()
        update_and_notify(84, f"🔀 Applying cinematic transitions to {len(processed_clips)} scenes...")
        from modules.transitions import get_random_transition, apply_transition

        loaded_clips = []
        for c in processed_clips:
            if os.path.exists(c) and os.path.getsize(c) > 10000:
                try:
                    loaded_clips.append(VideoFileClip(c))
                except Exception as ve:
                    safe_print(f"⚠️ Warning: skipping corrupt scene chunk '{c}': {ve}")

        if loaded_clips:
            last_trans = None
            cur_clip = loaded_clips[0]
            for idx_t in range(1, len(loaded_clips)):
                next_clip = loaded_clips[idx_t]
                chosen_trans = get_random_transition(exclude=[last_trans])
                last_trans = chosen_trans
                cur_clip = apply_transition(cur_clip, next_clip, chosen_trans, duration=trans_dur)

            t_trans = time.time() - t_start_trans
            safe_print(f"  ✅ Transitions completed in {t_trans:.2f}s")

            master_write_kwargs = dict(
                codec=codec,
                audio=False,
                fps=FPS,
                bitrate=DEFAULT_BITRATE,
                ffmpeg_params=ffmpeg_params,
                logger="bar",
            )
            if codec == "libx264":
                master_write_kwargs["preset"] = DEFAULT_PRESET

            cur_clip.write_videofile(unmuxed_video_path, **master_write_kwargs)
            cur_clip.close()
            for c in loaded_clips:
                try: c.close()
                except: pass

    if not os.path.exists(unmuxed_video_path):
        # Fast Stream Copy Concat
        update_and_notify(84, f"⚡ Joining {len(processed_clips)} scene video chunks (fast stream copy)...")
        concat_list_path = os.path.join(TEMP_DIR, "video_concat_list.txt")
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for cfile in processed_clips:
                escaped = cfile.replace("\\", "/").replace("'", "\\'")
                f.write(f"file '{escaped}'\n")

        concat_cmd = [
            ffmpeg_exe, "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list_path,
            "-c", "copy",
            unmuxed_video_path
        ]
        subprocess.run(concat_cmd, capture_output=True, timeout=120)

    if not os.path.exists(unmuxed_video_path):
        # MoviePy Fallback Concat
        loaded_clips = [VideoFileClip(c) for c in processed_clips if os.path.exists(c)]
        comp = concatenate_videoclips(loaded_clips, method="compose")
        master_write_kwargs = dict(
            codec=codec,
            audio=False,
            fps=FPS,
            bitrate=DEFAULT_BITRATE,
            ffmpeg_params=ffmpeg_params,
            logger="bar",
        )
        if codec == "libx264":
            master_write_kwargs["preset"] = DEFAULT_PRESET
        comp.write_videofile(unmuxed_video_path, **master_write_kwargs)
        comp.close()

    # ── Direct FFmpeg Audio Mux ─────────────────────────────────────────────────
    update_and_notify(90, "🎤 Attaching uploaded audio directly to edited video...")
    safe_print("🎤 Attaching uploaded audio directly to edited video (zero audio mixing)...")

    mux_cmd = [
        ffmpeg_exe, "-y",
        "-i", unmuxed_video_path,
        "-i", uploaded_audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        final_output_path,
    ]

    safe_print("⚡ Running direct FFmpeg audio-video mux...")
    res = subprocess.run(mux_cmd, capture_output=True, timeout=180)

    if not os.path.exists(final_output_path) or os.path.getsize(final_output_path) < 10000:
        safe_print("⚠️ FFmpeg stream copy notice — attempting re-encode mux...")
        mux_cmd_re = [
            ffmpeg_exe, "-y",
            "-i", unmuxed_video_path,
            "-i", uploaded_audio_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-shortest",
            final_output_path,
        ]
        subprocess.run(mux_cmd_re, capture_output=True, timeout=180)

    total_time = time.time() - start_time
    safe_print(f"\n🎉 Done: {final_output_path}  (Total time: {fmt_time(total_time)})")

    # ── Temp Cleanup ───────────────────────────────────────────────────────────
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