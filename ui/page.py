"""
ui/page.py
─────────────────────────────────────────────────────────────────────────────
Main page layout for Pixelab — Audio-First Workflow.
Upload your audio voiceover (MP3 / WAV / M4A / OGG / FLAC / AAC).
Whisper AI transcribes the audio, extracts word-level timestamps, and syncs
kinetic subtitles + Pexels HD video cuts to your voice.
─────────────────────────────────────────────────────────────────────────────
"""
import os
import time
import streamlit as st

from modules.ai_director  import analyze_transcript, generate_video_brief
from modules.compositor   import build_master_video, build_master_video_from_audio
from modules.transcribe_engine import transcribe_audio
from modules.scene_splitter    import split_into_scenes
from modules.subtitle_vfx      import generate_live_preview_frame
from ui.progress_tracker  import ProgressTracker
from config import OUTPUT_DIR, TEMP_DIR


def _inject_api_keys(keys: dict):
    """Push active API keys into os.environ so modules can read them."""
    for env_name, value in keys.items():
        if value:
            os.environ[env_name] = value


def _save_uploaded_audio(uploaded_file) -> str | None:
    """
    Saves a Streamlit UploadedFile to a persistent temp path in OUTPUT_DIR.
    Returns the absolute file path on success, or None on failure.
    """
    try:
        ext = os.path.splitext(uploaded_file.name)[-1].lower() or ".mp3"
        save_path = os.path.join(OUTPUT_DIR, f"uploaded_audio{ext}")
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return save_path
    except Exception as e:
        st.error(f"❌ Failed to save uploaded audio: {e}")
        return None


def _render_live_preview_section(video_config: dict, api_keys: dict):
    """
    Renders an interactive Live Preview panel.
    Updates instantly (~10ms) whenever the user modifies sidebar settings.
    Includes a 3-second quick video clip sampler.
    """
    with st.expander("👁️ Real-Time Live Style & Subtitle Preview (Instant Updates)", expanded=True):
        col_img, col_ctrl = st.columns([1.6, 1])

        with col_ctrl:
            st.markdown("##### ⚙️ Subtitle & Style Live Tester")
            test_text = st.text_input(
                "💬 Custom Test Sentence:",
                value="NEON CITIES ARE EXPANDING ACROSS THE WORLD TODAY 🔥",
                help="Type any sentence to see font, size, position, active word glow, and emojis live."
            )
            words = [w for w in test_text.split() if w]
            max_idx = max(len(words), 1)
            active_idx = st.slider("Highlight Word Index", 1, max_idx, min(3, max_idx))

            st.caption(f"📐 **Ratio:** {video_config.get('aspect_ratio', '').split('(')[0].strip()}")
            st.caption(f"🍿 **Cinematic Bundle:** {video_config.get('cinematic_package', 'Custom')}")
            st.caption(f"🎨 **Color Grade:** {video_config.get('color_grade', 'None')}")
            st.caption(f"💬 **Typography Package:** {video_config.get('subtitle_package', 'Custom')}")
            st.caption(f"💬 **Font & Size:** {video_config.get('font', 'Default')} ({video_config.get('size', 42)}pt)")
            st.caption(f"📍 **Text Position:** {video_config.get('position', 'Bottom')}")

            # 3-Second Quick Clip Sampler
            if st.button("⚡ Render 3-Sec Quick Preview Clip", use_container_width=True, help="Renders a 3-second sample clip to preview motion, audio sync, and transitions in ~3s"):
                with st.spinner("⚡ Rendering 3-second sample clip..."):
                    _inject_api_keys(api_keys)
                    test_scenes = [{
                        "narration": test_text,
                        "search_query": "futuristic city",
                    }]
                    preview_out = os.path.join(OUTPUT_DIR, "quick_preview.mp4")
                    cfg = dict(video_config)
                    cfg["enable_bg_music"] = False  # Keep test clip light
                    success = build_master_video(test_scenes, cfg, output_filename="quick_preview.mp4")
                    if success and os.path.exists(preview_out):
                        st.session_state["quick_preview_video"] = preview_out
                        st.success("✅ 3-Second Sample Clip Ready!")
                    else:
                        st.error("⚠️ Quick preview generation notice — try regular video render.")

            if st.session_state.get("quick_preview_video") and os.path.exists(st.session_state["quick_preview_video"]):
                st.video(st.session_state["quick_preview_video"])

        with col_img:
            # Generate instant preview frame (~10ms)
            try:
                preview_frame = generate_live_preview_frame(
                    video_config,
                    sample_text=test_text,
                    active_word_index=active_idx - 1
                )
                st.image(
                    preview_frame,
                    caption=f"Live Preview | {video_config.get('aspect_ratio', '')} | Grade: {video_config.get('color_grade', 'None')}",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Preview render notice: {e}")

    st.divider()


def render_page(sidebar_data: dict, api_keys: dict, keys_ready: bool):
    """
    Renders the main page — Audio Upload & Video Generation.
    """
    video_config  = sidebar_data["video_config"]
    scene_count   = sidebar_data["scene_count"]
    ai_tone       = sidebar_data["ai_tone"]
    fps_choice    = sidebar_data["fps_choice"]
    aspect_ratio  = sidebar_data["aspect_ratio"]
    color_grade   = sidebar_data["color_grade"]
    sub_style     = sidebar_data["sub_style"]

    # ── Real-Time Live Visual & Subtitle Preview Engine ───────────────────────
    _render_live_preview_section(video_config, api_keys)

    # ════════════════════════════════════════════════════════════════════════
    # AUDIO UPLOAD WORKFLOW
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        "### 🎤 Upload Your Audio Voiceover\n"
        "Upload a pre-recorded MP3, WAV, M4A, OGG, or FLAC audio file. "
        "Whisper AI transcribes your voice, extracts word-level timestamps, "
        "and syncs kinetic subtitles + Pexels HD video cuts to your narration."
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "🎵 Audio File (MP3 / WAV / M4A / OGG / FLAC / AAC — max 200 MB)",
            type=["mp3", "wav", "m4a", "ogg", "flac", "aac"],
            help="Your voiceover audio will be used as-is in the final video.",
        )

    with col2:
        st.markdown("**⚙️ Quick Settings**")
        st.caption(f"📐 {aspect_ratio.split('(')[0].strip()}")
        st.caption(f"🎨 Grade: {color_grade}")
        st.caption(f"💬 Style: {sub_style}")
        st.caption(f"🤖 Tone: {ai_tone}")
        st.caption(f"🎬 Scenes: {scene_count}")

    if uploaded_file is not None:
        st.audio(uploaded_file, format=uploaded_file.type)
        st.success(
            f"✅ **{uploaded_file.name}** uploaded "
            f"({uploaded_file.size / 1024 / 1024:.1f} MB) — "
            f"Ready to render {scene_count} scenes."
        )
    else:
        st.info(
            f"📁 Upload an audio file above to begin.  \n"
            f"Will split into **{scene_count} scenes** with kinetic subtitle sync."
        )

    st.info(
        f"🎬 Will generate **{scene_count} scenes** from your audio | "
        f"Tone: **{ai_tone}** | "
        f"FPS: **{fps_choice}** | "
        f"Subtitles synced to your voice timestamps"
    )

    render_disabled = not keys_ready or (uploaded_file is None)
    render_tooltip  = (
        "Upload an audio file first." if uploaded_file is None
        else "API keys missing." if not keys_ready
        else ""
    )

    col_ub1, col_ub2 = st.columns([1, 1])
    with col_ub1:
        btn_u_quick = st.button(
            "⚡ TEST 3-SEC SAMPLE VIDEO",
            type="secondary",
            disabled=(uploaded_file is None),
            use_container_width=True,
            help="Renders a 3-second sample clip using your uploaded audio"
        )
    with col_ub2:
        btn_u_full = st.button(
            "🚀 RENDER FULL VIDEO WITH UPLOADED AUDIO",
            type="primary",
            disabled=render_disabled,
            use_container_width=True,
            help=render_tooltip,
        )

    run_u_quick = btn_u_quick or st.session_state.pop("trigger_quick_test", False)

    if not run_u_quick and not btn_u_full:
        return

    if run_u_quick:
        _inject_api_keys(api_keys)
        audio_path = _save_uploaded_audio(uploaded_file)
        if not audio_path:
            return
        with st.spinner("⚡ Transcribing audio snippet & rendering 3-second sample clip..."):
            t_res = transcribe_audio(audio_path)
            full_txt = t_res.get("full_text", "") or "Sample audio voiceover"
            w_ts = t_res.get("word_timestamps", [])
            tot_dur = t_res.get("total_duration", 3.0)
            sub_scenes = split_into_scenes(w_ts, tot_dur, scene_count=1)
            sub_scenes = analyze_transcript(sub_scenes, api_keys.get("GROQ_API_KEY", ""), tone=video_config["ai_tone"])
            if sub_scenes:
                sub_scenes[0]["end_sec"] = min(sub_scenes[0]["start_sec"] + 3.0, tot_dur)
            cfg = dict(video_config)
            cfg["enable_bg_music"] = False
            quick_out = os.path.join(OUTPUT_DIR, "quick_preview.mp4")
            success = build_master_video_from_audio(sub_scenes, audio_path, cfg, output_filename="quick_preview.mp4")
            if success and os.path.exists(quick_out):
                st.success("✅ **3-Second Sample Video Ready!** Watch below to check your color grade, subtitle style, and audio sync:")
                st.video(quick_out)
            else:
                st.error("❌ Quick sample render failed.")
        return

    # ── Save uploaded file to disk ─────────────────────────────────────
    _inject_api_keys(api_keys)
    audio_path = _save_uploaded_audio(uploaded_file)
    if not audio_path:
        return

    # ── Transcription ──────────────────────────────────────────────────
    tracker = ProgressTracker(scene_count)

    st.subheader("📡 Live Generation & Render Tracker")
    progress_bar = st.progress(0.0)

    # ── DEBUG: Show API key & audio file status ────────────────────────
    groq_key    = api_keys.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")
    el_key      = api_keys.get("ELEVENLABS_API_KEY", "") or os.environ.get("ELEVENLABS_API_KEY", "")
    audio_exists = os.path.exists(audio_path)
    audio_size   = os.path.getsize(audio_path) if audio_exists else 0

    with st.expander("🔧 Debug Info (transcription)", expanded=True):
        st.write(f"🔑 GROQ_API_KEY set: `{'✅ Yes' if groq_key else '❌ NO — this is the problem!'}`")
        st.write(f"🔑 ELEVENLABS_API_KEY set: `{'✅ Yes' if el_key else '❌ No'}`")
        st.write(f"🎵 Audio saved to disk: `{'✅ Yes' if audio_exists else '❌ NO'}`")
        st.write(f"📦 Audio file size: `{audio_size/1024:.1f} KB`")
        st.write(f"📁 Audio path: `{audio_path}`")

    status_box = st.info("🎙️ Step 1/4 — Transcribing your audio with Groq Whisper...")

    with st.spinner("🔍 Transcribing audio... (may take 10–60s for large files)"):
        transcript_result = transcribe_audio(audio_path)

    full_text       = transcript_result["full_text"]
    word_timestamps = transcript_result["word_timestamps"]
    total_duration  = transcript_result["total_duration"]
    method          = transcript_result["method"]

    progress_bar.progress(0.12)

    if not full_text and not total_duration:
        status_box.error(
            "❌ Could not read the audio file at all. "
            "Please make sure the file is a valid MP3, WAV, or M4A."
        )
        return

    if not full_text:
        status_box.warning(
            "⚠️ Whisper could not transcribe text from this audio.  \n"
            "The video will still be rendered with your audio, but subtitles "
            "will not be shown."
        )
        word_timestamps = []

    # ── Show transcription preview ─────────────────────────────────────
    with st.expander(
        f"📝 Transcription Preview ({len(word_timestamps)} words | "
        f"{total_duration:.1f}s | method: {method})",
        expanded=True,
    ):
        st.write(full_text)
        if method == "linear_fallback":
            st.warning(
                "⚠️ Whisper not installed — using linear interpolation for word timing.  \n"
                "For accurate subtitle sync: `pip install openai-whisper`"
            )

    # ── Split into scenes ──────────────────────────────────────────────
    status_box.info("🎬 Step 2/4 — Splitting audio into scenes...")
    progress_bar.progress(0.18)

    scenes = split_into_scenes(word_timestamps, total_duration, scene_count)

    # ── AI Director (search queries only) ─────────────────────────────
    status_box.info(
        f"🤖 Step 3/4 — AI Director generating search queries for {len(scenes)} scenes..."
    )
    progress_bar.progress(0.22)

    groq_key = api_keys.get("GROQ_API_KEY", "")
    video_brief = generate_video_brief(full_text, groq_key)

    scenes = analyze_transcript(
        scenes,
        groq_key,
        tone=video_config["ai_tone"],
        video_brief=video_brief,
    )

    progress_bar.progress(0.28)
    status_box.success(
        f"✅ Ready! {len(scenes)} scenes | {total_duration:.1f}s audio | "
        f"Starting video render..."
    )

    # Show scene breakdown before render
    with st.expander("🎬 Scene Breakdown", expanded=False):
        for i, sc in enumerate(scenes, start=1):
            st.markdown(
                f"**Scene {i}** ({sc['start_sec']:.1f}s – {sc['end_sec']:.1f}s, "
                f"{sc['end_sec']-sc['start_sec']:.1f}s) | "
                f"🔍 `{sc['search_query']}` | "
                f"*\"{sc['narration'][:80]}...\"*"
            )

    # ── Phase: Build video ─────────────────────────────────────────────
    tracker = ProgressTracker(scene_count)

    c1, c2, c3, c4, c5 = st.columns(5)
    tracker.done_metric    = c1.empty()
    tracker.fail_metric    = c2.empty()
    tracker.pend_metric    = c3.empty()
    tracker.elapsed_metric = c4.empty()
    tracker.eta_metric     = c5.empty()
    tracker.tracker_ph     = st.empty()
    tracker.progress_bar   = progress_bar
    tracker.status_box     = status_box
    tracker._update_metrics(done=0, failed=0, left=scene_count, elapsed=0, eta="—")

    callback = tracker.make_callback()
    out_path = os.path.join(OUTPUT_DIR, "final_video.mp4")
    t0       = time.time()

    success = build_master_video_from_audio(
        scenes=scenes,
        uploaded_audio_path=audio_path,
        config=video_config,
        output_filename="final_video.mp4",
        progress_callback=callback,
    )

    total_time = time.time() - t0
    tracker.show_result(
        success=success and os.path.exists(out_path),
        out_path=out_path if success else None,
        total_time=total_time,
        scenes=scenes,
    )
